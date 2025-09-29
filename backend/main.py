import os
import uuid
import base64
from datetime import datetime
from typing import List, Optional

import pandas as pd
from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .db import Base, engine, SessionLocal, Dataset, ChatHistory, PlotHistory
from .helpers import (
    load_dataframe,
    merge_datasets,
    preprocess_dataset,
    visual_summary_local,
    generate_plot_local,
    cross_file_plot,
    ai_analysis_gemini
)

# ------------------- Config -------------------
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="EDA Agent API", version="1.0")

# ------------------- CORS -------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- DB Dependency -------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------- Endpoints -------------------

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    dataset = Dataset(
        file_id=file_id,
        filename=file.filename,
        file_path=file_path,
        upload_time=datetime.utcnow()
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return {"status": "success", "file_id": file_id, "filename": file.filename}


@app.get("/datasets")
def list_datasets(db: Session = Depends(get_db)):
    datasets = db.query(Dataset).all()
    return [
        {"file_id": d.file_id, "filename": d.filename, "uploaded": d.upload_time}
        for d in datasets
    ]


@app.post("/merge")
def merge_files(
    file_ids: List[str] = Form(...),
    on: Optional[str] = Form(None),
    how: str = Form("inner"),
    db: Session = Depends(get_db)
):
    dfs = []
    for fid in file_ids:
        dataset = db.query(Dataset).filter(Dataset.file_id == fid).first()
        if dataset:
            dfs.append(load_dataframe(dataset.file_path))

    merged_df = merge_datasets(dfs, on=on, how=how)
    merged_file = f"merged_{uuid.uuid4().hex}.csv"
    merged_path = os.path.join(UPLOAD_DIR, merged_file)
    merged_df.to_csv(merged_path, index=False)

    return {"status": "success", "merged_file": merged_file}


@app.post("/preprocess")
def preprocess_file(
    file_id: str = Form(...),
    missing: str = Form("mean"),
    scaling: str = Form("none"),
    outlier: str = Form("none"),
    encode: str = Form("none"),
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.file_id == file_id).first()
    if not dataset:
        return JSONResponse(status_code=404, content={"error": "File not found"})

    df = load_dataframe(dataset.file_path)
    df_processed = preprocess_dataset(df, missing, scaling, outlier, encode)

    out_file = f"preprocessed_{uuid.uuid4().hex}.csv"
    out_path = os.path.join(UPLOAD_DIR, out_file)
    df_processed.to_csv(out_path, index=False)

    return {"status": "success", "processed_file": out_file}


@app.get("/visual_summary/{file_id}")
def visual_summary(file_id: str, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.file_id == file_id).first()
    if not dataset:
        return JSONResponse(status_code=404, content={"error": "File not found"})

    df = load_dataframe(dataset.file_path)
    figs = visual_summary_local(df)
    plots_data = []

    for name, fig in figs:
        img_bytes = fig.to_image(format="png")
        img_b64 = base64.b64encode(img_bytes).decode()
        plots_data.append({"name": name, "image": img_b64})

        db_plot = PlotHistory(plot_name=name, plot_type="summary", plot_base64=img_b64)
        db.add(db_plot)

    db.commit()
    return plots_data


@app.post("/plot")
def custom_plot(
    file_id: str = Form(...),
    plot_type: str = Form(...),
    x: Optional[str] = Form(None),
    y: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.file_id == file_id).first()
    if not dataset:
        return JSONResponse(status_code=404, content={"error": "File not found"})

    df = load_dataframe(dataset.file_path)
    fig = generate_plot_local(df, plot_type, x, y, color)
    img_bytes = fig.to_image(format="png")
    img_b64 = base64.b64encode(img_bytes).decode()

    db_plot = PlotHistory(
        plot_name=f"{plot_type}_{uuid.uuid4().hex}",
        plot_type=plot_type,
        plot_base64=img_b64
    )
    db.add(db_plot)
    db.commit()

    return {"image": img_b64}


@app.post("/cross_plot")
def cross_plot(
    file_ids: List[str] = Form(...),
    x: str = Form(...),
    y: str = Form(...),
    db: Session = Depends(get_db)
):
    dfs = []
    for fid in file_ids:
        dataset = db.query(Dataset).filter(Dataset.file_id == fid).first()
        if dataset:
            dfs.append(load_dataframe(dataset.file_path))

    fig = cross_file_plot(dfs, x, y)
    img_bytes = fig.to_image(format="png")
    img_b64 = base64.b64encode(img_bytes).decode()

    return {"image": img_b64}


@app.post("/chat")
def chat_with_ai(
    file_id: str = Form(...),
    query: str = Form(...),
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.file_id == file_id).first()
    if not dataset:
        return JSONResponse(status_code=404, content={"error": "File not found"})

    df = load_dataframe(dataset.file_path)
    response = ai_analysis_gemini(df, query)

    chat_entry = ChatHistory(user_query=query, ai_response=response)
    db.add(chat_entry)
    db.commit()

    return {"response": response}
