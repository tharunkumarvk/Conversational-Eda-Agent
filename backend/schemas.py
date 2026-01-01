# backend/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# Authentication Schemas
class GoogleLoginRequest(BaseModel):
    token: str  # Google OAuth ID token from frontend

class UserResponse(BaseModel):
    id: int
    google_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime
    last_login: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Existing Schemas
class FileUploadResponse(BaseModel):
    status: str
    file_id: str
    filename: str
    size: int
    message: str = "File uploaded successfully"

class DatasetInfo(BaseModel):
    file_id: str
    filename: str
    uploaded: datetime
    rows: Optional[int] = None
    columns: Optional[int] = None
    size: Optional[int] = None

class MergeRequest(BaseModel):
    file_ids: List[str] = Field(..., min_items=2, max_items=2, description="Exactly 2 file IDs required")
    left_on: str = Field(..., description="Column name from left dataset")
    right_on: str = Field(..., description="Column name from right dataset")
    how: str = Field("inner", pattern="^(inner|outer|left|right)$")
    fuzzy: bool = False
    fuzzy_threshold: int = Field(80, ge=0, le=100)

class PreprocessRequest(BaseModel):
    file_id: str
    missing: str = Field("mean", pattern="^(mean|median|mode|drop|knn|iterative)$")
    cat_missing: str = Field("mode", pattern="^(mode|constant)$")
    scaling: str = Field("none", pattern="^(none|standard|minmax|robust)$")
    outlier: str = Field("none", pattern="^(none|zscore|iqr|isolation)$")
    outlier_action: str = Field("cap", pattern="^(cap|remove|transform)$")
    encode: str = Field("none", pattern="^(none|onehot|label|ordinal|binary|frequency)$")
    reduce_dims: bool = False
    red_method: str = Field("pca", pattern="^(pca|tsne|svd|lda)$")
    n_components: int = Field(2, ge=1, le=50)
    feature_selection: bool = False
    sel_method: str = Field("variance", pattern="^(variance|kbest)$")
    
class PlotRequest(BaseModel):
    file_id: str
    plot_type: str = Field(..., description="Type of plot to generate")
    x: Optional[str] = None
    y: Optional[str] = None
    z: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    title: Optional[str] = None
    
    @validator('plot_type')
    def validate_plot_type(cls, v):
        allowed = [
            'auto', 'scatter', 'scatter3d', 'line', 'line3d', 'bar', 'bar_polar', 
            'histogram', 'box', 'violin', 'heatmap', 'pie', 'sunburst', 'treemap',
            'funnel', 'density_contour', 'correlation'
        ]
        if v not in allowed:
            raise ValueError(f'plot_type must be one of {allowed}')
        return v

class ChatRequest(BaseModel):
    file_id: str
    query: str = Field(..., min_length=1, max_length=2000)

class ChatResponse(BaseModel):
    response: str
    timestamp: datetime
    query: str

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SuccessResponse(BaseModel):
    status: str = "success"
    message: str
    data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DataProfileResponse(BaseModel):
    file_id: str
    filename: str
    shape: tuple
    columns: List[str]
    dtypes: dict
    missing_values: dict
    statistics: dict
    quality_score: float
