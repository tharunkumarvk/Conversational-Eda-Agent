"""
Data Utilities Module
Handles data loading, preprocessing, and transformations
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import streamlit as st
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.ensemble import IsolationForest


@dataclass
class FileMetadata:
    """Metadata for uploaded files"""
    name: str
    shape: Tuple[int, int]
    columns: list
    dtypes: Dict[str, str]
    missing_count: dict
    uploaded_at: str
    file_size: int


def load_file(file_buffer) -> Optional[pd.DataFrame]:
    """Load CSV or Excel file from buffer"""
    try:
        if file_buffer.name.endswith('.csv'):
            return pd.read_csv(file_buffer)
        elif file_buffer.name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file_buffer)
    except Exception as e:
        st.error(f"Error loading {file_buffer.name}: {e}")
        return None


def create_metadata(df: pd.DataFrame, name: str, file_size: int = 0) -> FileMetadata:
    """Create metadata for a dataframe"""
    return FileMetadata(
        name=name,
        shape=df.shape,
        columns=df.columns.tolist(),
        dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
        missing_count={col: int(df[col].isna().sum()) for col in df.columns},
        uploaded_at=datetime.now().isoformat(),
        file_size=file_size or int(df.memory_usage(deep=True).sum())
    )


def get_column_info(df: pd.DataFrame) -> Dict[str, Any]:
    """Get comprehensive column information"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
    
    return {
        "numeric": numeric_cols,
        "categorical": categorical_cols,
        "datetime": datetime_cols,
        "all": df.columns.tolist()
    }


def handle_missing_values(df: pd.DataFrame, strategy: str = "mean", columns: list = None) -> pd.DataFrame:
    """Handle missing values in dataframe"""
    df_clean = df.copy()
    cols = columns or df.columns.tolist()
    
    numeric_cols = df_clean[cols].select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df_clean[cols].select_dtypes(include=['object']).columns.tolist()
    
    if strategy == "drop":
        df_clean = df_clean.dropna(subset=cols)
    
    elif strategy in ["mean", "median", "most_frequent"]:
        if numeric_cols:
            imputer = SimpleImputer(strategy=strategy if strategy != "most_frequent" else "mean")
            df_clean[numeric_cols] = imputer.fit_transform(df_clean[numeric_cols])
        
        if categorical_cols:
            imputer = SimpleImputer(strategy="most_frequent")
            df_clean[categorical_cols] = imputer.fit_transform(df_clean[categorical_cols])
    
    elif strategy == "knn":
        if numeric_cols:
            imputer = KNNImputer(n_neighbors=5)
            df_clean[numeric_cols] = imputer.fit_transform(df_clean[numeric_cols])
    
    return df_clean


def handle_outliers(df: pd.DataFrame, method: str = "iqr", columns: list = None) -> pd.DataFrame:
    """Handle outliers in numerical columns"""
    df_clean = df.copy()
    numeric_cols = columns or df_clean.select_dtypes(include=[np.number]).columns.tolist()
    
    if method == "iqr":
        for col in numeric_cols:
            Q1 = df_clean[col].quantile(0.25)
            Q3 = df_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df_clean[col] = df_clean[col].clip(lower=lower_bound, upper=upper_bound)
    
    elif method == "zscore":
        for col in numeric_cols:
            mean = df_clean[col].mean()
            std = df_clean[col].std()
            df_clean[col] = df_clean[col].clip(lower=mean - 3*std, upper=mean + 3*std)
    
    elif method == "isolation_forest":
        if numeric_cols:
            iso = IsolationForest(contamination=0.1, random_state=42)
            outlier_mask = iso.fit_predict(df_clean[numeric_cols]) == 1
            df_clean = df_clean[outlier_mask]
    
    return df_clean


def scale_features(df: pd.DataFrame, method: str = "standard", columns: list = None) -> pd.DataFrame:
    """Scale numerical features"""
    df_scaled = df.copy()
    numeric_cols = columns or df_scaled.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        return df_scaled
    
    if method == "standard":
        scaler = StandardScaler()
    elif method == "minmax":
        scaler = MinMaxScaler()
    else:
        return df_scaled
    
    df_scaled[numeric_cols] = scaler.fit_transform(df_scaled[numeric_cols])
    return df_scaled


def encode_categorical(df: pd.DataFrame, method: str = "label", columns: list = None) -> pd.DataFrame:
    """Encode categorical features"""
    df_encoded = df.copy()
    categorical_cols = columns or df_encoded.select_dtypes(include=['object']).columns.tolist()
    
    if not categorical_cols:
        return df_encoded
    
    if method == "label":
        for col in categorical_cols:
            le = LabelEncoder()
            df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
    
    elif method == "onehot":
        df_encoded = pd.get_dummies(df_encoded, columns=categorical_cols, prefix=categorical_cols)
    
    return df_encoded


def merge_datasets(df1: pd.DataFrame, df2: pd.DataFrame, on: str = None, how: str = "inner") -> pd.DataFrame:
    """Merge two datasets"""
    try:
        if on:
            return pd.merge(df1, df2, on=on, how=how)
        else:
            common_cols = list(set(df1.columns) & set(df2.columns))
            if common_cols:
                return pd.merge(df1, df2, on=common_cols[0], how=how)
            else:
                st.error("No common columns found for merging")
                return None
    except Exception as e:
        st.error(f"Merge error: {e}")
        return None


def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Get comprehensive data summary"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    summary = {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.to_dict(),
        "missing": df.isnull().sum().to_dict(),
        "missing_pct": (df.isnull().sum() / len(df) * 100).to_dict(),
        "duplicates": df.duplicated().sum(),
        "memory_mb": df.memory_usage(deep=True).sum() / 1024**2
    }
    
    if numeric_cols:
        summary["statistics"] = df[numeric_cols].describe().to_dict()
        summary["correlations"] = df[numeric_cols].corr().to_dict()
    
    return summary


def detect_data_quality_issues(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect common data quality issues"""
    issues = {
        "missing_values": {},
        "duplicates": df.duplicated().sum(),
        "constant_columns": [],
        "high_cardinality": []
    }
    
    # Missing values
    missing = df.isnull().sum()
    issues["missing_values"] = {col: int(count) for col, count in missing.items() if count > 0}
    
    # Constant columns
    for col in df.columns:
        if df[col].nunique() == 1:
            issues["constant_columns"].append(col)
    
    # High cardinality categorical
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() > 0.5 * len(df):
            issues["high_cardinality"].append(col)
    
    return issues
