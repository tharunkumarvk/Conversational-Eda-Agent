# backend/main.py
import os
import uuid
import base64
import traceback
from datetime import datetime
from typing import List, Optional
from pathlib import Path

# CRITICAL: Load .env BEFORE any other imports to override system env vars
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except Exception:
    pass

import pandas as pd
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Optional rate limiting
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    print("⚠️ slowapi not available - rate limiting disabled")

from .config import settings
from .logger import logger
from .db import Base, engine, SessionLocal, Dataset, ChatHistory, PlotHistory, User
from .storage import init_storage, upload_file_to_storage, download_to_temp_file, cleanup_temp_file
from .auth import verify_google_token, get_or_create_user, create_access_token, get_current_user
from .schemas import (
    FileUploadResponse, DatasetInfo, MergeRequest, PreprocessRequest,
    PlotRequest, ChatRequest, ChatResponse, ErrorResponse, SuccessResponse,
    DataProfileResponse, GoogleLoginRequest, TokenResponse, UserResponse
)
from .helpers import (
    load_dataframe,
    merge_datasets,
    preprocess_dataset,
    visual_summary_local,
    generate_plot_local,
    cross_file_plot,
    ai_analysis_gemini,
    ai_analysis_gemini_agentic,
    generate_data_profile
)

# ------------------- Config -------------------
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize Supabase Storage
STORAGE_ENABLED = init_storage()
if STORAGE_ENABLED:
    logger.info("✅ Supabase Storage enabled - files will be stored in cloud")
else:
    logger.info("⚠️ Supabase Storage disabled - files will be stored locally")

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize rate limiter (if available)
if SLOWAPI_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
else:
    limiter = None

# Create FastAPI app
app = FastAPI(
    title="EDA Agent API",
    version="2.0.0",
    description="Production-grade EDA Agent with AI capabilities",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add rate limiter to app state (if available)
if limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Helper function for optional rate limiting
def apply_rate_limit():
    """Decorator that applies rate limiting only if slowapi is available"""
    def decorator(func):
        if limiter and SLOWAPI_AVAILABLE:
            return limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")(func)
        return func
    return decorator

# ------------------- Middleware -------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# ------------------- Exception Handlers -------------------
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc) if settings.ENVIRONMENT == "development" else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ------------------- DB Dependency -------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------- Helper Functions -------------------
def validate_file_extension(filename: str) -> bool:
    """Validate file has allowed extension"""
    return any(filename.lower().endswith(ext) for ext in settings.ALLOWED_EXTENSIONS)

def get_dataset_or_404(db: Session, file_id: str, user_id: int = None) -> Dataset:
    """Get dataset or raise 404, optionally verify ownership"""
    query = db.query(Dataset).filter(Dataset.file_id == file_id)
    
    # If user_id provided, verify ownership
    if user_id is not None:
        query = query.filter(Dataset.user_id == user_id)
    
    dataset = query.first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with file_id {file_id} not found or you don't have access"
        )
    return dataset

# ------------------- Endpoints -------------------

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check"""
    return {
        "status": "online",
        "service": "EDA Agent API",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """Detailed health check"""
    try:
        # Check database
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# ------------------- Authentication Endpoints -------------------

@app.post("/api/auth/google", response_model=TokenResponse, tags=["Authentication"])
async def google_login(login_data: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user with Google OAuth token and return JWT
    """
    try:
        # Verify Google token and get user info
        google_user_info = await verify_google_token(login_data.token)
        
        # Get or create user in database
        user = get_or_create_user(db, google_user_info)
        
        # Create JWT token
        access_token = create_access_token(data={"user_id": user.id})
        
        # Prepare user response
        user_response = UserResponse(
            id=user.id,
            google_id=user.google_id,
            email=user.email,
            name=user.name,
            picture=user.picture,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
        logger.info(f"User authenticated: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

@app.get("/api/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return UserResponse(
        id=current_user.id,
        google_id=current_user.google_id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@app.post("/api/auth/logout", tags=["Authentication"])
async def logout():
    """
    Logout endpoint (client should delete token)
    """
    return {"message": "Logged out successfully"}

# ------------------- File Upload Endpoints -------------------

@app.post("/api/upload", response_model=FileUploadResponse, tags=["Files"])
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a CSV or Excel file for analysis (requires authentication)"""
    try:
        logger.info(f"User {current_user.email} uploading file: {file.filename}")
        
        # Validate file extension
        if not validate_file_extension(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE / 1024**2}MB"
            )
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        storage_filename = f"{file_id}_{file.filename}"
        
        # Try to upload to Supabase Storage first (if enabled)
        if STORAGE_ENABLED:
            success, result = upload_file_to_storage(
                file_content=content,
                filename=storage_filename,
                content_type=file.content_type or "text/csv"
            )
            
            if success:
                file_storage_path = result  # Supabase public URL
                logger.info(f"File uploaded to Supabase Storage: {storage_filename}")
            else:
                # Fallback to local storage
                logger.warning(f"Supabase upload failed, using local storage: {result}")
                file_storage_path = str(UPLOAD_DIR / storage_filename)
                with open(file_storage_path, "wb") as f:
                    f.write(content)
        else:
            # Local storage (original behavior)
            file_storage_path = str(UPLOAD_DIR / storage_filename)
            with open(file_storage_path, "wb") as f:
                f.write(content)
        
        # Validate the dataframe (download temporarily if in cloud)
        try:
            if file_storage_path.startswith("http"):
                # File is in Supabase, download temporarily to validate
                success, temp_path, error = download_to_temp_file(storage_filename)
                if not success:
                    raise Exception(f"Failed to download for validation: {error}")
                try:
                    df = load_dataframe(temp_path)
                    rows, cols = df.shape
                finally:
                    cleanup_temp_file(temp_path)
            else:
                # Local file
                df = load_dataframe(file_storage_path)
                rows, cols = df.shape
        except Exception as e:
            # Clean up on validation failure
            if not file_storage_path.startswith("http"):
                Path(file_storage_path).unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format or corrupted file: {str(e)}"
            )
        
        # Save to database with user_id
        dataset = Dataset(
            file_id=file_id,
            filename=file.filename,
            file_path=file_storage_path,  # Can be URL or local path
            upload_time=datetime.utcnow(),
            rows=rows,
            columns=cols,
            size_bytes=file_size,
            user_id=current_user.id  # Associate with authenticated user
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        storage_location = "cloud" if file_storage_path.startswith("http") else "local"
        logger.info(f"File uploaded successfully ({storage_location}): {file_id}")
        
        return FileUploadResponse(
            status="success",
            file_id=file_id,
            filename=file.filename,
            size=file_size,
            message=f"File uploaded successfully to {storage_location} storage. {rows} rows, {cols} columns"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@app.get("/api/datasets", response_model=List[DatasetInfo], tags=["Files"])
async def list_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all datasets for the authenticated user"""
    try:
        # Filter datasets by user_id
        datasets = db.query(Dataset).filter(
            Dataset.user_id == current_user.id
        ).order_by(Dataset.upload_time.desc()).all()
        
        return [
            DatasetInfo(
                file_id=d.file_id,
                filename=d.filename,
                uploaded=d.upload_time,
                rows=d.rows,
                columns=d.columns,
                size=d.size_bytes
            )
            for d in datasets
        ]
    except Exception as e:
        logger.error(f"Error listing datasets for user {current_user.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve datasets"
        )

@app.get("/api/dataset/{file_id}", tags=["Files"])
async def get_dataset_info(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a dataset (requires authentication)"""
    dataset = get_dataset_or_404(db, file_id, user_id=current_user.id)
    
    try:
        df = load_dataframe(dataset.file_path)
        profile = generate_data_profile(df)
        
        return {
            "file_id": dataset.file_id,
            "filename": dataset.filename,
            "uploaded": dataset.upload_time,
            "profile": profile
        }
    except Exception as e:
        logger.error(f"Error getting dataset info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dataset profile"
        )

@app.delete("/api/dataset/{file_id}", tags=["Files"])
async def delete_dataset(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a dataset (requires authentication)"""
    dataset = get_dataset_or_404(db, file_id, user_id=current_user.id)
    
    try:
        # Delete file from disk
        if os.path.exists(dataset.file_path):
            os.remove(dataset.file_path)
        
        # Delete from database
        db.delete(dataset)
        db.commit()
        
        logger.info(f"Dataset deleted: {file_id}")
        return {"status": "success", "message": "Dataset deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting dataset: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete dataset"
        )

@app.post("/api/merge", tags=["Processing"])
async def merge_files(
    merge_req: MergeRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Merge multiple datasets"""
    try:
        logger.info(f"User {current_user.email} merging files: {merge_req.file_ids}")
        
        # Load all dataframes - verify user owns them
        dfs = []
        filenames = []
        for fid in merge_req.file_ids:
            dataset = get_dataset_or_404(db, fid, user_id=current_user.id)
            dfs.append(load_dataframe(dataset.file_path))
            filenames.append(dataset.filename)
        
        # Merge datasets with optional fuzzy matching
        merged_df = merge_datasets(
            dfs, 
            left_on=merge_req.left_on,
            right_on=merge_req.right_on,
            how=merge_req.how,
            fuzzy=merge_req.fuzzy,
            fuzzy_threshold=merge_req.fuzzy_threshold
        )
        
        # Save merged file
        merged_file_id = str(uuid.uuid4())
        merged_filename = f"merged_{'_'.join([f.split('.')[0] for f in filenames[:3]])}.csv"
        merged_path = UPLOAD_DIR / f"{merged_file_id}_{merged_filename}"
        merged_df.to_csv(merged_path, index=False)
        
        # Save to database
        rows, cols = merged_df.shape
        dataset = Dataset(
            file_id=merged_file_id,
            filename=merged_filename,
            file_path=str(merged_path),
            upload_time=datetime.utcnow(),
            rows=rows,
            columns=cols,
            size_bytes=os.path.getsize(merged_path)
        )
        db.add(dataset)
        db.commit()
        
        logger.info(f"Files merged successfully: {merged_file_id}")
        
        return {
            "status": "success",
            "file_id": merged_file_id,
            "filename": merged_filename,
            "rows": rows,
            "columns": cols,
            "message": f"Successfully merged {len(dfs)} files"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Merge error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Merge failed: {str(e)}"
        )

@app.post("/api/preprocess", tags=["Processing"])
async def preprocess_file(
    preprocess_req: PreprocessRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preprocess a dataset with various transformations"""
    dataset = get_dataset_or_404(db, preprocess_req.file_id, user_id=current_user.id)
    
    try:
        logger.info(f"Preprocessing file: {preprocess_req.file_id}")
        
        # Load dataframe
        df = load_dataframe(dataset.file_path)
        
        # Apply preprocessing with all parameters
        df_processed = preprocess_dataset(
            df,
            missing=preprocess_req.missing,
            cat_missing=preprocess_req.cat_missing,
            scaling=preprocess_req.scaling,
            outlier=preprocess_req.outlier,
            outlier_action=preprocess_req.outlier_action,
            encode=preprocess_req.encode,
            reduce_dims=preprocess_req.reduce_dims,
            red_method=preprocess_req.red_method,
            n_components=preprocess_req.n_components,
            feature_selection=preprocess_req.feature_selection,
            sel_method=preprocess_req.sel_method
        )
        
        # Save processed file
        processed_file_id = str(uuid.uuid4())
        processed_filename = f"preprocessed_{dataset.filename}"
        processed_path = UPLOAD_DIR / f"{processed_file_id}_{processed_filename}"
        df_processed.to_csv(processed_path, index=False)
        
        # Save to database
        rows, cols = df_processed.shape
        new_dataset = Dataset(
            file_id=processed_file_id,
            filename=processed_filename,
            file_path=str(processed_path),
            upload_time=datetime.utcnow(),
            rows=rows,
            columns=cols,
            size_bytes=os.path.getsize(processed_path)
        )
        db.add(new_dataset)
        db.commit()
        
        logger.info(f"Preprocessing completed: {processed_file_id}")
        
        return {
            "status": "success",
            "file_id": processed_file_id,
            "filename": processed_filename,
            "original_shape": df.shape,
            "processed_shape": df_processed.shape,
            "message": "Preprocessing completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preprocessing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preprocessing failed: {str(e)}"
        )

@app.get("/api/visual_summary/{file_id}", tags=["Visualization"])
async def visual_summary(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate automatic visual summary of dataset"""
    dataset = get_dataset_or_404(db, file_id, user_id=current_user.id)
    
    try:
        logger.info(f"User {current_user.email} generating visual summary: {file_id}")
        
        df = load_dataframe(dataset.file_path)
        figs = visual_summary_local(df)
        plots_data = []
        
        for name, fig in figs:
            try:
                img_bytes = fig.to_image(format="png")
                img_b64 = base64.b64encode(img_bytes).decode()
                plots_data.append({"name": name, "image": img_b64})
            except Exception as e:
                logger.warning(f"Failed to generate plot {name}: {e}")
                continue
        
        logger.info(f"Visual summary generated: {len(plots_data)} plots")
        return {"plots": plots_data, "count": len(plots_data)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Visual summary error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate visual summary: {str(e)}"
        )

@app.post("/api/plot", tags=["Visualization"])
async def custom_plot(
    plot_req: PlotRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate custom plot"""
    dataset = get_dataset_or_404(db, plot_req.file_id, user_id=current_user.id)
    
    try:
        logger.info(f"Generating plot: {plot_req.plot_type} for {plot_req.file_id}")
        
        df = load_dataframe(dataset.file_path)
        fig = generate_plot_local(
            df,
            plot_type=plot_req.plot_type,
            x=plot_req.x,
            y=plot_req.y,
            color=plot_req.color
        )
        
        img_bytes = fig.to_image(format="png")
        img_b64 = base64.b64encode(img_bytes).decode()
        
        plot_name = f"{plot_req.plot_type}_{uuid.uuid4().hex[:8]}"
        
        # Save plot to database
        plot_history = PlotHistory(
            file_id=plot_req.file_id,
            plot_name=plot_name,
            plot_type=plot_req.plot_type,
            plot_base64=img_b64,
            user_id=current_user.id,
            ts=datetime.utcnow()
        )
        db.add(plot_history)
        db.commit()
        
        logger.info(f"Plot generated and saved successfully: {plot_name}")
        return {"image": img_b64, "plot_name": plot_name}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plot generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate plot: {str(e)}"
        )

@app.post("/api/chat", response_model=ChatResponse, tags=["AI"])
async def chat_with_ai(
    chat_req: ChatRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with AI about your dataset - with agentic plot generation"""
    dataset = get_dataset_or_404(db, chat_req.file_id, user_id=current_user.id)
    
    try:
        logger.info(f"AI chat query: {chat_req.query[:50]}... for {chat_req.file_id}")
        
        df = load_dataframe(dataset.file_path)
        
        # Use special agentic version that can save plots
        response = ai_analysis_gemini_agentic(df, chat_req.query, chat_req.file_id, db, current_user.id)
        
        # Save to chat history
        chat_history = ChatHistory(
            user_query=chat_req.query,
            ai_response=response,
            file_id=chat_req.file_id,
            user_id=current_user.id,
            ts=datetime.utcnow()
        )
        db.add(chat_history)
        db.commit()
        
        logger.info(f"AI response generated and saved successfully")
        
        return ChatResponse(
            response=response,
            timestamp=datetime.utcnow(),
            query=chat_req.query
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(e)}"
        )

@app.get("/api/chat/history/{file_id}", tags=["AI"])
async def get_chat_history(
    file_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat history for a dataset"""
    try:
        history = (
            db.query(ChatHistory)
            .filter(
                ChatHistory.file_id == file_id,
                ChatHistory.user_id == current_user.id
            )
            .order_by(ChatHistory.ts.desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                "query": h.user_query,
                "response": h.ai_response,
                "timestamp": h.ts
            }
            for h in reversed(history)
        ]
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )

@app.get("/api/plots/{file_id}", tags=["Visualization"])
async def get_saved_plots(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all saved plots for a dataset from PlotHistory"""
    try:
        # Verify dataset exists
        dataset = get_dataset_or_404(db, file_id, user_id=current_user.id)
        
        # Retrieve all plots for this file_id and user
        plots = db.query(PlotHistory).filter(
            PlotHistory.file_id == file_id,
            PlotHistory.user_id == current_user.id
        ).order_by(PlotHistory.ts.desc()).all()
        
        if not plots:
            return JSONResponse(content={
                "file_id": file_id,
                "count": 0,
                "plots": [],
                "message": "No plots found for this dataset"
            })
        
        # Format plot data
        plot_data = []
        for plot in plots:
            plot_data.append({
                "id": plot.id,
                "plot_name": plot.plot_name,
                "plot_type": plot.plot_type,
                "plot_base64": plot.plot_base64,
                "timestamp": plot.ts.isoformat() if plot.ts else None
            })
        
        logger.info(f"Retrieved {len(plot_data)} plots for file_id: {file_id}")
        return JSONResponse(content={
            "file_id": file_id,
            "dataset_name": dataset.filename,
            "count": len(plot_data),
            "plots": plot_data
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving plots: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve plots: {str(e)}"
        )

@app.get("/api/plots/{file_id}/download", tags=["Visualization"])
async def download_all_plots(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download all plots as a ZIP file"""
    import zipfile
    from io import BytesIO
    
    try:
        # Verify dataset exists
        dataset = get_dataset_or_404(db, file_id, user_id=current_user.id)
        
        # Retrieve all plots for this file_id and user
        plots = db.query(PlotHistory).filter(
            PlotHistory.file_id == file_id,
            PlotHistory.user_id == current_user.id
        ).all()
        
        if not plots:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No plots found for this dataset"
            )
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for idx, plot in enumerate(plots):
                # Decode base64 to binary
                img_data = base64.b64decode(plot.plot_base64)
                
                # Sanitize filename
                safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in plot.plot_name)
                filename = f"{idx+1:02d}_{safe_name}.png"
                
                # Add to ZIP
                zip_file.writestr(filename, img_data)
        
        # Prepare response
        zip_buffer.seek(0)
        
        logger.info(f"Created ZIP with {len(plots)} plots for file_id: {file_id}")
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={dataset.filename}_plots.zip"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating plot ZIP: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create plot ZIP: {str(e)}"
        )

@app.delete("/api/plots/{file_id}", tags=["Visualization"])
async def delete_saved_plots(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete all saved plots for a dataset"""
    try:
        # Verify dataset exists
        dataset = get_dataset_or_404(db, file_id, user_id=current_user.id)
        
        # Delete all plots for this file_id and user
        deleted_count = db.query(PlotHistory).filter(
            PlotHistory.file_id == file_id,
            PlotHistory.user_id == current_user.id
        ).delete()
        db.commit()
        
        logger.info(f"Deleted {deleted_count} plots for file_id: {file_id}")
        return JSONResponse(content={
            "file_id": file_id,
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} plots"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting plots: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete plots: {str(e)}"
        )

@app.get("/api/download/{file_id}", tags=["Files"])
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a processed file"""
    dataset = get_dataset_or_404(db, file_id, user_id=current_user.id)
    
    if not os.path.exists(dataset.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=dataset.file_path,
        filename=dataset.filename,
        media_type="application/octet-stream"
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("EDA Agent API starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    logger.info(f"Database: {settings.DATABASE_URL}")
    
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("EDA Agent API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )
