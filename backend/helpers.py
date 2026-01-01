# backend/helpers.py
import os
import io
import json
import re
import uuid
import base64
import traceback
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import (StandardScaler, MinMaxScaler, RobustScaler, 
                                  PowerTransformer, OrdinalEncoder, LabelEncoder, 
                                  OneHotEncoder, LabelBinarizer, PolynomialFeatures)
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_selection import VarianceThreshold, SelectKBest, chi2
from sklearn.manifold import TSNE
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
try:
    from imblearn.over_sampling import SMOTE
    from imblearn.under_sampling import RandomUnderSampler
    IMBLEARN_AVAILABLE = True
except ImportError:
    IMBLEARN_AVAILABLE = False

# Fuzzy matching (optional - will handle import error gracefully)
try:
    from fuzzywuzzy import process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

# Supabase Storage
try:
    from .storage import download_to_temp_file, cleanup_temp_file
    STORAGE_AVAILABLE = True
except ImportError:
    try:
        from storage import download_to_temp_file, cleanup_temp_file
        STORAGE_AVAILABLE = True
    except ImportError:
        STORAGE_AVAILABLE = False
        print("⚠️ Storage module not available")

# Gemini
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    genai = None
    GENAI_AVAILABLE = False

# dotenv support
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # Override system env vars with .env file
except Exception:
    pass

# init gemini if available
GENAI = None
def init_genai():
    global GENAI
    if not GENAI_AVAILABLE:
        GENAI = None
        print("⚠️ Gemini not available (module not installed)")
        return
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        GENAI = None
        print("⚠️ GOOGLE_API_KEY not found in environment")
        return
    try:
        # Log the API key being used (first 20 chars for security)
        print(f"✅ Using GOOGLE_API_KEY: {key[:20]}... (length: {len(key)})")
        genai.configure(api_key=key)
        GENAI = genai
        print("✅ Gemini configured successfully")
    except Exception as e:
        GENAI = None
        print(f"❌ Failed to configure Gemini: {e}")

init_genai()

# ---- Basic IO / loading ----
def load_dataframe(path: str) -> pd.DataFrame:
    """Load dataframe from local file or Supabase Storage URL"""
    path = str(path)
    
    # Check if it's a Supabase Storage URL
    if path.startswith("http"):
        if not STORAGE_AVAILABLE:
            raise ValueError("Storage module not available for cloud files")
        
        # Extract filename from URL
        filename = path.split("/")[-1].split("?")[0]  # Remove query params
        
        # Download to temporary file
        success, temp_path, error = download_to_temp_file(filename)
        if not success:
            raise ValueError(f"Failed to download file from storage: {error}")
        
        try:
            # Load from temp file
            if filename.lower().endswith(".csv"):
                df = pd.read_csv(temp_path)
            elif filename.lower().endswith((".xls", ".xlsx")):
                df = pd.read_excel(temp_path)
            else:
                raise ValueError(f"Unsupported file type: {filename}")
            return df
        finally:
            # Always cleanup temp file
            cleanup_temp_file(temp_path)
    
    # Local file
    if path.lower().endswith(".csv"):
        return pd.read_csv(path)
    if path.lower().endswith((".xls", ".xlsx")):
        return pd.read_excel(path)
    raise ValueError("Unsupported file type: " + path)

# ---- Merge multiple datasets with fuzzy matching ----
def merge_datasets(dfs: List[pd.DataFrame], left_on: str, right_on: str, how: str = "inner", fuzzy: bool = False, fuzzy_threshold: int = 80) -> pd.DataFrame:
    """Merge two dataframes with support for different column names and fuzzy matching"""
    if not dfs or len(dfs) < 2:
        raise ValueError("Need at least 2 dataframes to merge")
    
    left_df = dfs[0].copy()
    right_df = dfs[1].copy()
    
    # Validate columns exist
    if left_on not in left_df.columns:
        raise ValueError(f"Column '{left_on}' not found in left dataset. Available: {list(left_df.columns)}")
    if right_on not in right_df.columns:
        raise ValueError(f"Column '{right_on}' not found in right dataset. Available: {list(right_df.columns)}")
    
    # Fuzzy matching
    if fuzzy and FUZZY_AVAILABLE:
        try:
            matches = []
            left_values = left_df[left_on].astype(str).tolist()
            right_values = right_df[right_on].astype(str).tolist()
            
            for idx_left, val_left in enumerate(left_values):
                best_match = process.extractOne(val_left, right_values)
                if best_match and best_match[1] >= fuzzy_threshold:
                    # Find the index in right_df where this match occurs
                    match_indices = right_df[right_df[right_on].astype(str) == best_match[0]].index.tolist()
                    if match_indices:
                        matches.append((idx_left, match_indices[0]))
            
            if not matches:
                raise ValueError(f"No fuzzy matches found with threshold {fuzzy_threshold}%")
            
            # Build matched dataframes
            left_indices = [m[0] for m in matches]
            right_indices = [m[1] for m in matches]
            left_matched = left_df.iloc[left_indices].reset_index(drop=True)
            right_matched = right_df.iloc[right_indices].reset_index(drop=True)
            
            # Merge on index
            result = pd.merge(left_matched, right_matched, left_index=True, right_index=True, 
                            how='inner', suffixes=('', '_right'))
            return result
        except Exception as e:
            raise ValueError(f"Fuzzy matching failed: {str(e)}")
    
    # Standard pandas merge
    try:
        result = pd.merge(left_df, right_df, left_on=left_on, right_on=right_on, 
                         how=how, suffixes=('', '_right'))
        return result
    except Exception as e:
        raise ValueError(f"Merge failed: {str(e)}")

# ---- Advanced Preprocessing ----
def preprocess_dataset(df: pd.DataFrame, 
                      missing: str = "mean", 
                      cat_missing: str = "mode",
                      scaling: str = "none", 
                      outlier: str = "none",
                      outlier_action: str = "cap",
                      encode: str = "none",
                      reduce_dims: bool = False,
                      red_method: str = "pca",
                      n_components: int = 2,
                      feature_selection: bool = False,
                      sel_method: str = "variance",
                      handle_imbalance: bool = False,
                      imbalance_method: str = "smote",
                      target_column: str = None,
                      polynomial_features: bool = False,
                      poly_degree: int = 2,
                      binning: bool = False,
                      bin_columns: list = None,
                      n_bins: int = 5) -> pd.DataFrame:
    """Advanced preprocessing with all Streamlit features including SMOTE, LDA, polynomial features, binning"""
    d = df.copy()
    num_cols = d.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = d.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    # 1. Handle missing values - NUMERIC
    if missing == "mean" and num_cols:
        d[num_cols] = d[num_cols].fillna(d[num_cols].mean())
    elif missing == "median" and num_cols:
        d[num_cols] = d[num_cols].fillna(d[num_cols].median())
    elif missing == "knn" and num_cols:
        imputer = KNNImputer(n_neighbors=5)
        d[num_cols] = imputer.fit_transform(d[num_cols])
    elif missing == "iterative" and num_cols:
        try:
            from sklearn.experimental import enable_iterative_imputer
            from sklearn.impute import IterativeImputer
            imputer = IterativeImputer(max_iter=10, random_state=42)
            d[num_cols] = imputer.fit_transform(d[num_cols])
        except:
            # Fallback to KNN if iterative not available
            imputer = KNNImputer(n_neighbors=5)
            d[num_cols] = imputer.fit_transform(d[num_cols])
    elif missing == "drop":
        d = d.dropna()

    # 1b. Handle missing values - CATEGORICAL
    if cat_missing == "mode" and cat_cols:
        for c in cat_cols:
            if d[c].isnull().any():
                mode_val = d[c].mode().iloc[0] if not d[c].mode().empty else "Unknown"
                d[c] = d[c].fillna(mode_val)
    elif cat_missing == "constant" and cat_cols:
        d[cat_cols] = d[cat_cols].fillna("Unknown")

    # 2. Handle outliers
    if outlier != "none" and num_cols:
        for col in num_cols:
            try:
                if outlier == "iqr":
                    Q1 = d[col].quantile(0.25)
                    Q3 = d[col].quantile(0.75)
                    IQR = Q3 - Q1
                    if IQR > 0:
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        outlier_mask = (d[col] < lower_bound) | (d[col] > upper_bound)
                        
                        if outlier_action == "cap":
                            d.loc[d[col] < lower_bound, col] = lower_bound
                            d.loc[d[col] > upper_bound, col] = upper_bound
                        elif outlier_action == "remove":
                            d = d[~outlier_mask]
                        elif outlier_action == "transform":
                            transformer = PowerTransformer(method='yeo-johnson')
                            d[[col]] = transformer.fit_transform(d[[col]])
                
                elif outlier == "zscore":
                    from scipy import stats
                    z_scores = np.abs(stats.zscore(d[col].dropna()))
                    if len(z_scores) > 0:
                        mean_val = d[col].mean()
                        std_val = d[col].std()
                        if outlier_action == "cap":
                            lower_bound = mean_val - 3 * std_val
                            upper_bound = mean_val + 3 * std_val
                            d.loc[d[col] < lower_bound, col] = lower_bound
                            d.loc[d[col] > upper_bound, col] = upper_bound
                
                elif outlier == "isolation":
                    iso = IsolationForest(contamination=0.05, random_state=42)
                    outliers = iso.fit_predict(d[[col]])
                    if outlier_action == "remove":
                        d = d[outliers != -1]
                    elif outlier_action == "cap":
                        lower, upper = d[col].quantile([0.01, 0.99])
                        d[col] = np.clip(d[col], lower, upper)
            except Exception:
                continue

    # 3. Encoding
    if encode != "none" and cat_cols:
        for c in cat_cols:
            try:
                if encode == "onehot":
                    dummies = pd.get_dummies(d[c], prefix=c, drop_first=False)
                    d = pd.concat([d.drop(c, axis=1), dummies], axis=1)
                elif encode == "label":
                    le = LabelEncoder()
                    d[c] = le.fit_transform(d[c].astype(str))
                elif encode == "ordinal":
                    oe = OrdinalEncoder()
                    d[c] = oe.fit_transform(d[[c]])
                elif encode == "binary" and d[c].nunique() == 2:
                    d[c] = (d[c] == d[c].unique()[0]).astype(int)
                elif encode == "frequency":
                    freq = d[c].value_counts(normalize=True)
                    d[c] = d[c].map(freq)
            except Exception:
                continue

    # Update numeric columns after encoding
    num_cols = d.select_dtypes(include=[np.number]).columns.tolist()

    # 4. Scaling
    if scaling != "none" and num_cols:
        if scaling == "standard":
            scaler = StandardScaler()
            d[num_cols] = scaler.fit_transform(d[num_cols])
        elif scaling == "minmax":
            scaler = MinMaxScaler()
            d[num_cols] = scaler.fit_transform(d[num_cols])
        elif scaling == "robust":
            scaler = RobustScaler()
            d[num_cols] = scaler.fit_transform(d[num_cols])

    # 5. Dimensionality Reduction
    if reduce_dims and num_cols and len(num_cols) > n_components:
        try:
            if red_method == "pca":
                pca = PCA(n_components=n_components)
                reduced = pca.fit_transform(d[num_cols])
                reduced_cols = [f'PCA_{i+1}' for i in range(n_components)]
                d = pd.concat([
                    d.drop(num_cols, axis=1), 
                    pd.DataFrame(reduced, columns=reduced_cols, index=d.index)
                ], axis=1)
            elif red_method == "tsne":
                tsne = TSNE(n_components=min(n_components, 3), random_state=42)
                reduced = tsne.fit_transform(d[num_cols])
                reduced_cols = [f'TSNE_{i+1}' for i in range(reduced.shape[1])]
                d = pd.concat([
                    d.drop(num_cols, axis=1),
                    pd.DataFrame(reduced, columns=reduced_cols, index=d.index)
                ], axis=1)
            elif red_method == "svd":
                svd = TruncatedSVD(n_components=n_components)
                reduced = svd.fit_transform(d[num_cols])
                reduced_cols = [f'SVD_{i+1}' for i in range(n_components)]
                d = pd.concat([
                    d.drop(num_cols, axis=1),
                    pd.DataFrame(reduced, columns=reduced_cols, index=d.index)
                ], axis=1)
            elif red_method == "lda" and target_column and target_column in d.columns:
                # LDA requires target variable for supervised dimensionality reduction
                try:
                    lda = LDA(n_components=min(n_components, len(d[target_column].unique()) - 1))
                    reduced = lda.fit_transform(d[num_cols], d[target_column])
                    reduced_cols = [f'LDA_{i+1}' for i in range(reduced.shape[1])]
                    d = pd.concat([
                        d.drop(num_cols, axis=1),
                        pd.DataFrame(reduced, columns=reduced_cols, index=d.index)
                    ], axis=1)
                except Exception as e:
                    print(f"LDA failed: {e}")
        except Exception:
            pass

    # 6. Feature Selection
    if feature_selection and num_cols and len(num_cols) > 1:
        try:
            if sel_method == "variance":
                selector = VarianceThreshold(threshold=0.01)
                selected_data = selector.fit_transform(d[num_cols])
                selected_cols = [num_cols[i] for i in selector.get_support(indices=True)]
                d = pd.concat([
                    d.drop(num_cols, axis=1),
                    pd.DataFrame(selected_data, columns=selected_cols, index=d.index)
                ], axis=1)
        except Exception:
            pass

    # 7. Handle Imbalanced Data (SMOTE)
    if handle_imbalance and target_column and target_column in d.columns and IMBLEARN_AVAILABLE:
        try:
            # Separate features and target
            X = d.drop(columns=[target_column])
            y = d[target_column]
            
            # Only apply SMOTE if target is categorical with at least 2 classes
            if y.nunique() >= 2 and y.nunique() < len(y) / 2:  # Not too many unique values
                if imbalance_method == "smote":
                    smote = SMOTE(random_state=42, k_neighbors=min(5, y.value_counts().min() - 1))
                    X_resampled, y_resampled = smote.fit_resample(X, y)
                    d = pd.concat([X_resampled, y_resampled], axis=1)
                elif imbalance_method == "undersample":
                    rus = RandomUnderSampler(random_state=42)
                    X_resampled, y_resampled = rus.fit_resample(X, y)
                    d = pd.concat([X_resampled, y_resampled], axis=1)
        except Exception as e:
            print(f"Imbalance handling failed: {e}")

    # 8. Polynomial Feature Engineering
    if polynomial_features and num_cols and len(num_cols) >= 2:
        try:
            poly = PolynomialFeatures(degree=poly_degree, include_bias=False)
            poly_features = poly.fit_transform(d[num_cols])
            poly_feature_names = poly.get_feature_names_out(num_cols)
            
            # Replace original numeric columns with polynomial features
            d = pd.concat([
                d.drop(num_cols, axis=1),
                pd.DataFrame(poly_features, columns=poly_feature_names, index=d.index)
            ], axis=1)
        except Exception as e:
            print(f"Polynomial features failed: {e}")

    # 9. Binning/Discretization
    if binning and bin_columns:
        try:
            for col in bin_columns:
                if col in d.columns and pd.api.types.is_numeric_dtype(d[col]):
                    d[f'{col}_binned'] = pd.qcut(d[col], q=n_bins, labels=False, duplicates='drop')
        except Exception as e:
            print(f"Binning failed: {e}")

    return d

# ---- Keep old function signature for backward compatibility ----
def preprocess_dataset_simple(df: pd.DataFrame, missing: str = "mean", scaling: str = "none", outlier: str = "none", encode: str = "none") -> pd.DataFrame:
    return preprocess_dataset(df, missing=missing, scaling=scaling, outlier=outlier, encode=encode)


# ---- Visual summary (fixed duplicate-name issue) ----
def visual_summary_local(df: pd.DataFrame, max_hist: int = 6) -> List[Tuple[str, object]]:
    figs = []
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    if len(num_cols) >= 2:
        fig = px.imshow(df[num_cols].corr().round(2), text_auto=True, title="Correlation heatmap")
        figs.append(("correlation", fig))

    for c in num_cols[:max_hist]:
        figs.append((f"hist_{c}", px.histogram(df, x=c, nbins=40, title=f"Histogram - {c}")))
        figs.append((f"box_{c}", px.box(df, y=c, title=f"Boxplot - {c}")))

    for c in cat_cols:
        try:
            vc = df[c].value_counts().reset_index()
            safe_count_col = f"count_{c}"
            vc.columns = [str(c), safe_count_col]
            figs.append((f"count_{c}", px.bar(vc, x=str(c), y=safe_count_col, title=f"Counts - {c}")))
        except Exception:
            # fallback: try simpler plot
            try:
                figs.append((f"count_{c}", px.histogram(df, x=c, title=f"Counts - {c}")))
            except Exception:
                pass

    return figs

# ---- Single-file plot generator (plotly) ----
def generate_plot_local(df: pd.DataFrame, plot_type: str = "auto", x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None):
    d = df.copy()
    num = d.select_dtypes(include=[np.number]).columns.tolist()
    cat = d.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    if plot_type == "auto":
        if x and y:
            plot_type = "scatter"
        elif len(num) == 1:
            plot_type = "hist"
        elif len(num) >= 2:
            plot_type = "scatter"
        elif cat:
            plot_type = "bar"
        else:
            plot_type = "hist"

    # Standard plots
    if plot_type == "scatter":
        if not x or not y:
            if len(num) >= 2:
                x, y = num[0], num[1]
            else:
                raise ValueError("Need two numeric columns for scatter")
        fig = px.scatter(d, x=x, y=y, color=color, title=f"Scatter: {x} vs {y}")
        return fig
    
    if plot_type == "scatter3d":
        if not x or not y or not z:
            if len(num) >= 3:
                x, y, z = num[0], num[1], num[2]
            else:
                raise ValueError("Need three numeric columns for 3D scatter")
        fig = px.scatter_3d(d, x=x, y=y, z=z, color=color, title=f"3D Scatter: {x}, {y}, {z}")
        return fig

    if plot_type in ("hist", "histogram"):
        if not x:
            x = num[0] if num else d.columns[0]
        fig = px.histogram(d, x=x, nbins=40, title=f"Histogram: {x}")
        return fig

    if plot_type == "line":
        fig = px.line(d, x=x or d.columns[0], y=y or d.columns[1] if len(d.columns) > 1 else d.columns[0], color=color, title="Line plot")
        return fig
    
    if plot_type == "line3d":
        if not x or not y or not z:
            if len(num) >= 3:
                x, y, z = num[0], num[1], num[2]
            else:
                raise ValueError("Need three numeric columns for 3D line")
        fig = px.line_3d(d, x=x, y=y, z=z, color=color, title=f"3D Line: {x}, {y}, {z}")
        return fig

    if plot_type in ("bar", "count"):
        fig = px.bar(d, x=x or (cat[0] if cat else d.columns[0]), y=y, color=color, title="Bar plot")
        return fig
    
    if plot_type == "bar_polar":
        if not x or not y:
            if cat and num:
                x, y = cat[0], num[0]
            else:
                raise ValueError("Need categorical and numeric columns for polar bar")
        fig = px.bar_polar(d, r=y, theta=x, color=color, title=f"Polar Bar: {x} vs {y}")
        return fig

    if plot_type == "box":
        fig = px.box(d, x=x, y=y, color=color, title="Box plot")
        return fig

    if plot_type == "violin":
        fig = px.violin(d, x=x, y=y, color=color, box=True, title="Violin plot")
        return fig

    if plot_type in ("heatmap", "correlation"):
        if len(num) < 2:
            raise ValueError("Not enough numeric columns for heatmap")
        corr = d[num].corr().round(2)
        fig = px.imshow(corr, text_auto=True, title="Correlation Heatmap", 
                       labels=dict(color="Correlation"))
        return fig
    
    if plot_type == "density_contour":
        if not x or not y:
            if len(num) >= 2:
                x, y = num[0], num[1]
            else:
                raise ValueError("Need two numeric columns for density contour")
        fig = px.density_contour(d, x=x, y=y, color=color, title=f"Density Contour: {x} vs {y}")
        return fig

    if plot_type == "pie":
        if not x:
            x = cat[0] if cat else d.columns[0]
        value_counts = d[x].value_counts()
        fig = px.pie(values=value_counts.values, names=value_counts.index, title=f"Pie: {x}")
        return fig
    
    if plot_type == "sunburst":
        if not x:
            x = cat[0] if cat else d.columns[0]
        # Create a hierarchical structure
        value_counts = d[x].value_counts().reset_index()
        value_counts.columns = ['category', 'count']
        fig = px.sunburst(value_counts, path=['category'], values='count', title=f"Sunburst: {x}")
        return fig
    
    if plot_type == "treemap":
        if not x:
            x = cat[0] if cat else d.columns[0]
        value_counts = d[x].value_counts().reset_index()
        value_counts.columns = ['category', 'count']
        fig = px.treemap(value_counts, path=['category'], values='count', title=f"Treemap: {x}")
        return fig
    
    if plot_type == "funnel":
        if not x or not y:
            if cat and num:
                x, y = cat[0], num[0]
            else:
                x, y = d.columns[0], d.columns[1] if len(d.columns) > 1 else d.columns[0]
        # Aggregate data for funnel
        funnel_data = d.groupby(x)[y].sum().reset_index() if y in num else d[x].value_counts().reset_index()
        if len(funnel_data.columns) == 2:
            funnel_data.columns = ['stage', 'value']
            fig = px.funnel(funnel_data, x='value', y='stage', title=f"Funnel: {x}")
            return fig
        else:
            raise ValueError("Could not create funnel chart with given columns")
    
    if plot_type == "waterfall":
        if not x or not y:
            if cat and num:
                x, y = cat[0], num[0]
            else:
                raise ValueError("Waterfall requires categorical (x) and numeric (y) columns")
        # Sample data if too many categories
        waterfall_data = d[[x, y]].dropna()
        if len(waterfall_data) > 20:
            waterfall_data = waterfall_data.head(20)
        
        fig = go.Figure(go.Waterfall(
            name="", orientation="v",
            measure=["relative"] * len(waterfall_data),
            x=waterfall_data[x],
            textposition="outside",
            text=waterfall_data[y].round(2),
            y=waterfall_data[y],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))
        fig.update_layout(title=f"Waterfall: {x} vs {y}")
        return fig
    
    if plot_type == "surface":
        if not x or not y or not color:
            if len(num) >= 3:
                x, y, color = num[0], num[1], num[2]
            else:
                raise ValueError("Surface plot requires three numeric columns (x, y, z)")
        # Create pivot table for surface
        try:
            pivot_df = d[[x, y, color]].dropna().pivot_table(values=color, index=y, columns=x, aggfunc='mean')
            fig = go.Figure(data=[go.Surface(z=pivot_df.values, x=pivot_df.columns, y=pivot_df.index)])
            fig.update_layout(title=f"Surface: {x}, {y}, {color}", scene=dict(xaxis_title=x, yaxis_title=y, zaxis_title=color))
            return fig
        except Exception as e:
            raise ValueError(f"Could not create surface plot: {str(e)}")
    
    # Seaborn/Matplotlib plots (return as matplotlib figures)
    if plot_type == "pairplot":
        numeric_cols_subset = num[:4] if len(num) > 4 else num  # Limit for performance
        if len(numeric_cols_subset) < 2:
            raise ValueError("Pairplot requires at least 2 numeric columns")
        pair_df = d[numeric_cols_subset].dropna()
        if len(pair_df) == 0:
            raise ValueError("No data available after removing missing values")
        sns.set_style("whitegrid")
        g = sns.pairplot(pair_df, diag_kind='hist')
        g.fig.suptitle("Pairplot", y=1.02)
        return g.fig
    
    if plot_type == "jointplot":
        if not x or not y:
            if len(num) >= 2:
                x, y = num[0], num[1]
            else:
                raise ValueError("Jointplot requires two numeric columns")
        clean_df = d[[x, y]].dropna()
        if len(clean_df) == 0:
            raise ValueError("No data available after removing missing values")
        g = sns.jointplot(data=clean_df, x=x, y=y, kind='scatter')
        g.fig.suptitle(f"Jointplot: {x} vs {y}", y=1.02)
        return g.fig
    
    if plot_type in ["kde", "kdeplot"]:
        if not x:
            x = num[0] if num else d.columns[0]
        clean_df = d[[x]].dropna()
        if len(clean_df) == 0:
            raise ValueError("No data available after removing missing values")
        fig_mpl, ax = plt.subplots(figsize=(10, 6))
        sns.kdeplot(data=clean_df, x=x, fill=True, ax=ax)
        ax.set_title(f"KDE Plot: {x}")
        plt.tight_layout()
        return fig_mpl
    
    if plot_type in ["dist", "distplot"]:
        if not x:
            x = num[0] if num else d.columns[0]
        clean_df = d[[x]].dropna()
        if len(clean_df) == 0:
            raise ValueError("No data available after removing missing values")
        fig_mpl, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(clean_df[x], kde=True, ax=ax)
        ax.set_title(f"Distribution Plot: {x}")
        plt.tight_layout()
        return fig_mpl
    
    if plot_type == "catplot":
        if not x:
            x = cat[0] if cat else d.columns[0]
        clean_df = d[[x, y] if y else [x]].dropna()
        if len(clean_df) == 0:
            raise ValueError("No data available after removing missing values")
        g = sns.catplot(data=clean_df, x=x, y=y, kind='strip', height=6, aspect=1.5)
        g.fig.suptitle(f"Catplot: {x}" + (f" vs {y}" if y else ""), y=1.02)
        return g.fig
    
    if plot_type == "countplot":
        if not x:
            x = cat[0] if cat else d.columns[0]
        clean_df = d[[x]].dropna()
        if len(clean_df) == 0:
            raise ValueError("No data available after removing missing values")
        if clean_df[x].nunique() > 20:
            clean_df = clean_df[clean_df[x].isin(clean_df[x].value_counts().head(20).index)]
        fig_mpl, ax = plt.subplots(figsize=(12, 6))
        sns.countplot(data=clean_df, x=x, ax=ax)
        ax.set_title(f"Count Plot: {x}")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        return fig_mpl

    raise ValueError("Unsupported plot type: " + str(plot_type))


# ---- Smart Auto-Visualization Generator ----
def create_smart_visualizations(df: pd.DataFrame, max_plots: int = 12) -> List[Tuple[str, Any]]:
    """Generate intelligent visualizations based on data characteristics (Streamlit feature)"""
    plots = []
    
    try:
        # Sample data if too large
        sample_df = df.sample(min(2000, len(df))) if len(df) > 2000 else df
        
        numeric_cols = sample_df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = sample_df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # 1. Correlation heatmap for numeric data
        if len(numeric_cols) >= 2:
            try:
                corr_matrix = sample_df[numeric_cols].corr()
                fig = px.imshow(corr_matrix.round(2), 
                               text_auto=True, 
                               color_continuous_scale='RdBu',
                               title="📊 Feature Correlation Matrix")
                plots.append(("Correlation Heatmap", fig))
            except Exception as e:
                print(f"Could not create correlation plot: {e}")
        
        # 2. Distribution plots for numeric columns (limit to first 3)
        for col in numeric_cols[:3]:
            try:
                fig = make_subplots(rows=1, cols=2, 
                                   subplot_titles=[f"Distribution - {col}", f"Box Plot - {col}"])
                
                # Histogram
                fig.add_trace(go.Histogram(x=sample_df[col], name="Distribution", nbinsx=30), row=1, col=1)
                
                # Box plot
                fig.add_trace(go.Box(y=sample_df[col], name="Box Plot"), row=1, col=2)
                
                fig.update_layout(title_text=f"📈 Distribution Analysis: {col}", showlegend=False, height=400)
                plots.append((f"Distribution - {col}", fig))
            except Exception as e:
                print(f"Could not create distribution plot for {col}: {e}")
        
        # 3. Category analysis for categorical columns (limit to first 2)
        for col in categorical_cols[:2]:
            try:
                if sample_df[col].nunique() <= 20:  # Only for reasonable number of categories
                    value_counts = sample_df[col].value_counts().head(10)
                    if len(value_counts) > 0:
                        fig = px.bar(x=value_counts.index, y=value_counts.values,
                                    title=f"📊 Top Categories: {col}",
                                    labels={'x': col, 'y': 'Count'})
                        fig.update_layout(xaxis_tickangle=-45)
                        plots.append((f"Categories - {col}", fig))
            except Exception as e:
                print(f"Could not create category plot for {col}: {e}")
        
        # 4. Scatter plots for numeric pairs (max 2)
        if len(numeric_cols) >= 2:
            for i in range(min(2, len(numeric_cols)-1)):
                try:
                    x_col, y_col = numeric_cols[i], numeric_cols[i+1]
                    fig = px.scatter(sample_df, x=x_col, y=y_col,
                                   title=f"🔗 Relationship: {x_col} vs {y_col}")
                    plots.append((f"Scatter - {x_col} vs {y_col}", fig))
                except Exception as e:
                    print(f"Could not create scatter plot: {e}")
        
        # 5. 3D scatter if enough numeric columns
        if len(numeric_cols) >= 3:
            try:
                fig = px.scatter_3d(sample_df, x=numeric_cols[0], y=numeric_cols[1], z=numeric_cols[2],
                                   title=f"3D Scatter: {numeric_cols[0]} vs {numeric_cols[1]} vs {numeric_cols[2]}")
                plots.append(("3D Scatter", fig))
            except Exception as e:
                print(f"Could not create 3D scatter: {e}")
        
        # 6. Box plot comparison (categorical vs numeric)
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            try:
                cat_col = categorical_cols[0]
                num_col = numeric_cols[0]
                if sample_df[cat_col].nunique() <= 10:
                    fig = px.box(sample_df, x=cat_col, y=num_col,
                               title=f"Box Plot: {cat_col} vs {num_col}")
                    fig.update_layout(xaxis_tickangle=-45)
                    plots.append((f"Box - {cat_col} vs {num_col}", fig))
            except Exception as e:
                print(f"Could not create box plot comparison: {e}")
        
        return plots[:max_plots]
    
    except Exception as e:
        print(f"Visualization creation failed: {e}")
        return []

# ---- Cross-file plotting: dfs is list of dataframes ----
def cross_file_plot(dfs: List[pd.DataFrame], left_col: str, right_col: str, plot_type: str = "scatter"):
    if not dfs or len(dfs) < 2:
        raise ValueError("Need at least two dataframes")
    left = dfs[0]
    right = dfs[1]
    # resolve column names index or name
    def resolve_col(df, c):
        if c is None:
            raise ValueError("Column identifier required")
        if str(c).isdigit():
            idx = int(c)
            return df.columns[idx]
        else:
            if c in df.columns:
                return c
            # try substring match
            for col in df.columns:
                if str(c).lower() in str(col).lower():
                    return col
            raise ValueError(f"Column {c} not found in dataframe")
    lc = resolve_col(left, left_col)
    rc = resolve_col(right, right_col)
    minlen = min(len(left), len(right))
    combined = pd.DataFrame({
        f"left__{lc}": left[lc].reset_index(drop=True).iloc[:minlen],
        f"right__{rc}": right[rc].reset_index(drop=True).iloc[:minlen]
    })
    if plot_type == "scatter":
        fig = px.scatter(combined, x=combined.columns[0], y=combined.columns[1], title=f"{lc} vs {rc} (cross-file)")
        return fig
    if plot_type == "bar":
        fig = px.bar(combined, x=combined.columns[0], y=combined.columns[1], title=f"{lc} vs {rc} (cross-file)")
        return fig
    return px.line(combined, title=f"{lc} vs {rc} (cross-file)")

# ---- Data Profiling ----
def generate_data_profile(df: pd.DataFrame) -> dict:
    """Generate comprehensive data profile"""
    try:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
        
        profile = {
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_values": df.isnull().sum().to_dict(),
            "missing_percentage": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
            "duplicate_rows": int(df.duplicated().sum()),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "statistics": {},
            "quality_score": 0.0
        }
        
        # Numeric statistics
        if numeric_cols:
            profile["statistics"]["numeric"] = df[numeric_cols].describe().to_dict()
        
        # Categorical statistics
        if categorical_cols:
            cat_stats = {}
            for col in categorical_cols[:10]:  # Limit to first 10
                try:
                    cat_stats[col] = {
                        "unique_count": int(df[col].nunique()),
                        "most_frequent": str(df[col].mode().iloc[0]) if not df[col].mode().empty else "N/A",
                        "top_5": df[col].value_counts().head(5).to_dict()
                    }
                except:
                    pass
            profile["statistics"]["categorical"] = cat_stats
        
        # Calculate quality score
        completeness = (1 - df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 40
        uniqueness = (1 - profile["duplicate_rows"] / max(df.shape[0], 1)) * 30
        volume = min(len(df) / 1000, 1) * 15
        features = min(len(df.columns) / 10, 1) * 15
        profile["quality_score"] = round(completeness + uniqueness + volume + features, 2)
        
        return profile
    except Exception as e:
        return {
            "shape": df.shape,
            "columns": [],
            "dtypes": {},
            "missing_values": {},
            "missing_percentage": {},
            "duplicate_rows": 0,
            "statistics": {},
            "quality_score": 0.0,
            "error": str(e)
        }

# ---- Tool Definitions for Agentic AI ----
def get_analysis_tools():
    """Define tools that the AI agent can use"""
    return [
        {
            "name": "get_data_summary",
            "description": "Get comprehensive statistical summary of the dataset including shape, missing values, data types, and basic statistics",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "preprocess_data",
            "description": "Preprocess the dataset by handling missing values, outliers, scaling, and encoding. Returns the processed data summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "missing": {
                        "type": "string",
                        "enum": ["mean", "median", "mode", "drop", "knn", "iterative"],
                        "description": "Method to handle missing values"
                    },
                    "scaling": {
                        "type": "string",
                        "enum": ["none", "standard", "minmax", "robust"],
                        "description": "Scaling method to apply"
                    },
                    "outlier": {
                        "type": "string",
                        "enum": ["none", "zscore", "iqr", "isolation"],
                        "description": "Outlier detection method"
                    },
                    "encode": {
                        "type": "string",
                        "enum": ["none", "onehot", "label", "ordinal"],
                        "description": "Encoding method for categorical variables"
                    }
                },
                "required": []
            }
        },
        {
            "name": "create_visualization",
            "description": "Create a visualization/plot from the dataset. Supports various chart types.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plot_type": {
                        "type": "string",
                        "enum": ["scatter", "line", "bar", "histogram", "box", "heatmap", "correlation", "3d_scatter"],
                        "description": "Type of plot to create"
                    },
                    "x": {
                        "type": "string",
                        "description": "Column name for X-axis"
                    },
                    "y": {
                        "type": "string",
                        "description": "Column name for Y-axis (optional for some plots)"
                    },
                    "color": {
                        "type": "string",
                        "description": "Column name for color grouping (optional)"
                    }
                },
                "required": ["plot_type"]
            }
        },
        {
            "name": "get_column_info",
            "description": "Get detailed information about specific columns including unique values, value counts, and distributions",
            "parameters": {
                "type": "object",
                "properties": {
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of column names to analyze"
                    }
                },
                "required": ["columns"]
            }
        },
        {
            "name": "filter_data",
            "description": "Filter the dataset based on conditions. Returns filtered data summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {
                        "type": "string",
                        "description": "Column name to filter on"
                    },
                    "condition": {
                        "type": "string",
                        "enum": [">", "<", ">=", "<=", "==", "!="],
                        "description": "Comparison operator"
                    },
                    "value": {
                        "type": "string",
                        "description": "Value to compare against"
                    }
                },
                "required": ["column", "condition", "value"]
            }
        }
    ]

def execute_tool(tool_name: str, parameters: dict, df: pd.DataFrame) -> str:
    """Execute a tool and return the result as a string"""
    try:
        if tool_name == "get_data_summary":
            summary = {
                "shape": df.shape,
                "columns": list(df.columns),
                "dtypes": df.dtypes.astype(str).to_dict(),
                "missing_values": df.isnull().sum().to_dict(),
                "basic_stats": df.describe(include='all').to_dict()
            }
            return json.dumps(summary, default=str, indent=2)
        
        elif tool_name == "preprocess_data":
            df_processed = preprocess_dataset(
                df,
                missing=parameters.get("missing", "mean"),
                scaling=parameters.get("scaling", "none"),
                outlier=parameters.get("outlier", "none"),
                encode=parameters.get("encode", "none")
            )
            result = {
                "status": "success",
                "original_shape": df.shape,
                "processed_shape": df_processed.shape,
                "message": "Data preprocessing completed",
                "preview": df_processed.head(3).to_dict(orient="records")
            }
            return json.dumps(result, default=str, indent=2)
        
        elif tool_name == "create_visualization":
            plot_type = parameters.get("plot_type", "scatter")
            x = parameters.get("x")
            y = parameters.get("y")
            color = parameters.get("color")
            
            # Validate columns exist
            if x and x not in df.columns:
                return f"Error: Column '{x}' not found. Available: {list(df.columns)}"
            if y and y not in df.columns:
                return f"Error: Column '{y}' not found. Available: {list(df.columns)}"
            
            result = {
                "status": "success",
                "plot_type": plot_type,
                "x_column": x,
                "y_column": y,
                "color": color,
                "message": f"Created {plot_type} visualization successfully. User can view it in the visualization panel."
            }
            return json.dumps(result, indent=2)
        
        elif tool_name == "get_column_info":
            columns = parameters.get("columns", [])
            info = {}
            for col in columns:
                if col in df.columns:
                    info[col] = {
                        "dtype": str(df[col].dtype),
                        "unique_values": int(df[col].nunique()),
                        "missing": int(df[col].isnull().sum()),
                        "sample_values": df[col].dropna().head(5).tolist() if len(df[col].dropna()) > 0 else []
                    }
                    if df[col].dtype in ['int64', 'float64']:
                        info[col]["stats"] = {
                            "mean": float(df[col].mean()),
                            "median": float(df[col].median()),
                            "std": float(df[col].std())
                        }
            return json.dumps(info, default=str, indent=2)
        
        elif tool_name == "filter_data":
            col = parameters.get("column")
            condition = parameters.get("condition")
            value = parameters.get("value")
            
            if col not in df.columns:
                return f"Error: Column '{col}' not found"
            
            # Convert value to appropriate type
            if df[col].dtype in ['int64', 'float64']:
                value = float(value)
            
            # Apply filter
            if condition == ">":
                filtered = df[df[col] > value]
            elif condition == "<":
                filtered = df[df[col] < value]
            elif condition == ">=":
                filtered = df[df[col] >= value]
            elif condition == "<=":
                filtered = df[df[col] <= value]
            elif condition == "==":
                filtered = df[df[col] == value]
            elif condition == "!=":
                filtered = df[df[col] != value]
            else:
                return f"Error: Invalid condition '{condition}'"
            
            result = {
                "status": "success",
                "original_rows": len(df),
                "filtered_rows": len(filtered),
                "filter": f"{col} {condition} {value}",
                "preview": filtered.head(3).to_dict(orient="records")
            }
            return json.dumps(result, default=str, indent=2)
        
        else:
            return f"Error: Unknown tool '{tool_name}'"
            
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"

# ---- Intent Detection and Action Execution ----
def detect_intent_and_execute(df: pd.DataFrame, query: str, file_id: str = None, db_session = None, user_id: int = None) -> tuple[str, list]:
    """Detect user intent from query and ACTUALLY EXECUTE actions like plot generation.
    Returns: (response_text, list_of_actions_performed)
    """
    query_lower = query.lower()
    actions_performed = []
    results = []
    
    # Intent: Data Summary / Info
    if any(word in query_lower for word in ['summary', 'describe', 'info', 'about', 'overview', 'tell me']):
        summary = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "basic_stats": df.describe(include='all').to_dict()
        }
        results.append(f"📊 **Dataset Summary**:\n- Shape: {df.shape[0]} rows × {df.shape[1]} columns\n- Columns: {', '.join(df.columns[:10])}")
        actions_performed.append("get_data_summary")
    
    # Intent: Visualization / Plot - ACTUALLY GENERATE AND SAVE PLOTS USING SMART VISUALIZATION
    if any(word in query_lower for word in ['plot', 'visual', 'chart', 'graph', 'show', 'display', 'summar']):
        import base64
        plots_generated = []
        plots_saved = 0
        
        # Generate comprehensive visualization set using smart auto-visualization
        if any(word in query_lower for word in ['all', 'every', 'comprehensive', 'summar', 'possible', 'auto']):
            try:
                # Use create_smart_visualizations for intelligent automatic plot generation
                smart_plots = create_smart_visualizations(df, max_plots=12)
                
                for plot_name, fig in smart_plots:
                    try:
                        if fig and db_session and file_id:
                            # Handle matplotlib figures (from seaborn)
                            if hasattr(fig, 'savefig'):
                                import io
                                buf = io.BytesIO()
                                fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                                plt.close(fig)
                                buf.seek(0)
                                img_b64 = base64.b64encode(buf.read()).decode()
                            # Handle plotly figures
                            else:
                                img_bytes = fig.to_image(format="png")
                                img_b64 = base64.b64encode(img_bytes).decode()
                            
                            from .db import PlotHistory
                            plot = PlotHistory(
                                plot_name=plot_name,
                                plot_type="auto",
                                plot_base64=img_b64,
                                file_id=file_id,
                                user_id=user_id
                            )
                            db_session.add(plot)
                            plots_saved += 1
                        plots_generated.append(plot_name)
                    except Exception as e:
                        print(f"Failed to save plot {plot_name}: {e}")
                
                if plots_saved > 0 and db_session:
                    db_session.commit()
                
                results.append(f"✅ **Generated {len(plots_generated)} smart visualizations** and saved {plots_saved} to database:\n" + 
                              "\n".join([f"- {p}" for p in plots_generated[:10]]))
                actions_performed.append(f"smart_auto_visualization_{plots_saved}_plots")
            except Exception as e:
                results.append(f"⚠️ Error generating smart visualizations: {str(e)}")
        
        # For specific plot requests, use the old manual approach
        elif any(word in query_lower for word in ['histogram', 'scatter', 'bar', 'line', 'heatmap']):
            num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            try:
                # 1. Histograms for numeric columns
                if 'histogram' in query_lower:
                    for col in num_cols[:3]:
                        try:
                            fig = generate_plot_local(df, plot_type="histogram", x=col)
                            if fig and db_session and file_id:
                                img_bytes = fig.to_image(format="png")
                                img_b64 = base64.b64encode(img_bytes).decode()
                                from .db import PlotHistory
                                plot = PlotHistory(
                                    plot_name=f"Histogram: {col}",
                                    plot_type="histogram",
                                    plot_base64=img_b64,
                                    file_id=file_id,
                                    user_id=user_id
                                )
                                db_session.add(plot)
                                plots_saved += 1
                            plots_generated.append(f"Histogram: {col}")
                        except Exception as e:
                            print(f"Failed histogram for {col}: {e}")
                
                # 2. Scatter plot
                if 'scatter' in query_lower and len(num_cols) >= 2:
                    try:
                        fig = generate_plot_local(df, plot_type="scatter", x=num_cols[0], y=num_cols[1])
                        if fig and db_session and file_id:
                            img_bytes = fig.to_image(format="png")
                            img_b64 = base64.b64encode(img_bytes).decode()
                            from .db import PlotHistory
                            plot = PlotHistory(
                                plot_name=f"Scatter: {num_cols[0]} vs {num_cols[1]}",
                                plot_type="scatter",
                                plot_base64=img_b64,
                                file_id=file_id,
                                user_id=user_id
                            )
                            db_session.add(plot)
                            plots_saved += 1
                        plots_generated.append(f"Scatter: {num_cols[0]} vs {num_cols[1]}")
                    except Exception as e:
                        print(f"Failed scatter plot: {e}")
                
                # 5. Box plots
                for col in num_cols[:3]:
                    try:
                        fig = generate_plot_local(df, plot_type="box", y=col)
                        if fig and db_session and file_id:
                            img_bytes = fig.to_image(format="png")
                            img_b64 = base64.b64encode(img_bytes).decode()
                            from .db import PlotHistory
                            plot = PlotHistory(
                                plot_name=f"Box Plot: {col}",
                                plot_type="box",
                                plot_base64=img_b64,
                                file_id=file_id,
                                user_id=user_id
                            )
                            db_session.add(plot)
                            plots_saved += 1
                        plots_generated.append(f"Box Plot: {col}")
                    except Exception as e:
                        print(f"Failed box plot for {col}: {e}")
                
                # Commit all plots to database
                if db_session and plots_saved > 0:
                    db_session.commit()
                    print(f"✅ Saved {plots_saved} plots to database")
                        
            except Exception as e:
                print(f"Error generating comprehensive plots: {e}")
                if db_session:
                    db_session.rollback()
            
            if plots_generated:
                results.append(f"✅ **Generated and saved {len(plots_generated)} visualizations**:\n" + 
                              "\n".join(f"- {p}" for p in plots_generated) +
                              f"\n\n💡 **{plots_saved} plots saved to database! View them in the Visualizations tab.**")
                actions_performed.append("created_visualizations")
            else:
                results.append("⚠️ **Could not auto-generate plots**. Please use the Visualization tab to create custom plots manually.")
        else:
            # Suggest specific plots based on data types
            plot_suggestions = []
            if num_cols:
                plot_suggestions.append(f"📈 For numerical columns ({', '.join(num_cols[:5])}): Histograms, Box plots, Scatter plots")
            if cat_cols:
                plot_suggestions.append(f"📊 For categorical columns ({', '.join(cat_cols[:5])}): Bar charts, Count plots")
            if len(num_cols) >= 2:
                plot_suggestions.append(f"🔗 Correlation heatmap for relationships")
                
            results.append("📊 **Visualization Recommendations**:\n" + "\n".join(plot_suggestions))
            results.append("\n💡 **To view plots**: Go to the 'Visualizations' tab and select your desired chart type with specific columns.")
            actions_performed.append("visual_recommendations")
    
    # Intent: Preprocessing - ACTUALLY EXECUTE PREPROCESSING
    if any(word in query_lower for word in ['preprocess', 'pre-process', 'clean', 'handle missing', 'scale', 'normalize', 'encode', 'impute', 'outlier', 'drop column', 'remove column']):
        try:
            # Determine preprocessing configuration based on query
            config = {
                'missing': 'median',  # default
                'cat_missing': 'mode',
                'scaling': 'none',
                'outlier': 'none',
                'encode': 'onehot',  # Default to onehot if user mentions categorical encoding
                'reduce_dims': False,
                'handle_imbalance': False,
            }
            
            # Adjust based on query keywords
            if 'mean' in query_lower:
                config['missing'] = 'mean'
            elif 'knn' in query_lower:
                config['missing'] = 'knn'
            elif 'iterative' in query_lower or 'mice' in query_lower:
                config['missing'] = 'iterative'
            
            if 'standard' in query_lower or 'z-score' in query_lower:
                config['scaling'] = 'standard'
            elif 'minmax' in query_lower or 'normalize' in query_lower:
                config['scaling'] = 'minmax'
            elif 'robust' in query_lower:
                config['scaling'] = 'robust'
            
            if 'iqr' in query_lower:
                config['outlier'] = 'iqr'
            elif 'zscore' in query_lower or 'z-score' in query_lower:
                config['outlier'] = 'zscore'
            elif 'isolation' in query_lower:
                config['outlier'] = 'isolation'
            
            # Enable encoding if categorical columns exist and user mentions encoding
            if any(word in query_lower for word in ['encode', 'encoding', 'categorical', 'one-hot', 'onehot']):
                if 'label' in query_lower and 'encod' in query_lower:
                    config['encode'] = 'label'
                elif 'ordinal' in query_lower:
                    config['encode'] = 'ordinal'
                else:
                    config['encode'] = 'onehot'  # Default to one-hot
            
            if 'pca' in query_lower:
                config['reduce_dims'] = True
                config['red_method'] = 'pca'
            elif 'tsne' in query_lower or 't-sne' in query_lower:
                config['reduce_dims'] = True
                config['red_method'] = 'tsne'
            
            # ACTUALLY PREPROCESS THE DATA
            preprocessed_df = preprocess_dataset(df.copy(), **config)
            
            # Drop columns if specifically mentioned
            cols_to_drop = []
            for col in df.columns:
                col_lower = col.lower()
                if any(drop_keyword in query_lower for drop_keyword in ['drop', 'remove', 'delete']):
                    if col_lower in query_lower or any(part in query_lower for part in col_lower.split('_')):
                        # Check for specific mentions
                        if 'cabin' in query_lower and 'cabin' in col_lower:
                            cols_to_drop.append(col)
                        elif 'passengerid' in query_lower.replace(' ', '') and 'passengerid' in col_lower.replace('_', ''):
                            cols_to_drop.append(col)
                        elif 'name' in query_lower and col_lower == 'name':
                            cols_to_drop.append(col)
                        elif 'ticket' in query_lower and 'ticket' in col_lower:
                            cols_to_drop.append(col)
            
            if cols_to_drop:
                preprocessed_df = preprocessed_df.drop(columns=[col for col in cols_to_drop if col in preprocessed_df.columns])
            
            # Save to database if db_session is available
            if db_session and file_id:
                import uuid
                from .db import Dataset
                
                new_file_id = str(uuid.uuid4())
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"preprocessed_{timestamp}_{file_id[:8]}.csv"
                new_filepath = os.path.join("uploaded_files", new_filename)
                
                # Ensure directory exists
                os.makedirs("uploaded_files", exist_ok=True)
                
                # Save preprocessed data
                preprocessed_df.to_csv(new_filepath, index=False)
                
                # Add to database
                new_dataset = Dataset(
                    file_id=new_file_id,
                    filename=new_filename,
                    file_path=new_filepath,
                    rows=len(preprocessed_df),
                    columns=len(preprocessed_df.columns),
                    size_bytes=os.path.getsize(new_filepath),
                    upload_time=datetime.now()
                )
                db_session.add(new_dataset)
                db_session.commit()
                
                # Build detailed report
                preprocessing_report = []
                preprocessing_report.append("✅ **PREPROCESSING COMPLETED!**")
                preprocessing_report.append(f"\n📊 **Original Shape**: {df.shape[0]} rows × {df.shape[1]} columns")
                preprocessing_report.append(f"📊 **Processed Shape**: {preprocessed_df.shape[0]} rows × {preprocessed_df.shape[1]} columns")
                preprocessing_report.append(f"\n💾 **New File Created**: `{new_filename}`")
                preprocessing_report.append(f"🆔 **New File ID**: `{new_file_id}`")
                
                preprocessing_report.append("\n🔧 **Operations Applied**:")
                if config['missing'] != 'none':
                    preprocessing_report.append(f"  - Missing values: {config['missing'].upper()} imputation")
                if config['cat_missing'] != 'none':
                    preprocessing_report.append(f"  - Categorical missing: {config['cat_missing'].upper()}")
                if cols_to_drop:
                    preprocessing_report.append(f"  - Dropped columns: {', '.join(cols_to_drop)}")
                if config['scaling'] != 'none':
                    preprocessing_report.append(f"  - Scaling: {config['scaling'].upper()}")
                if config['outlier'] != 'none':
                    preprocessing_report.append(f"  - Outliers: {config['outlier'].upper()} detection + capping")
                if config['encode'] != 'none':
                    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                    if cat_cols:
                        preprocessing_report.append(f"  - Encoding: {config['encode'].upper()} applied to {len(cat_cols)} categorical columns")
                if config['reduce_dims']:
                    preprocessing_report.append(f"  - Dimensionality reduction: {config.get('red_method', 'PCA').upper()}")
                
                preprocessing_report.append("\n📥 **How to Access**:")
                preprocessing_report.append(f"  1. Go to Dashboard - file appears automatically")
                preprocessing_report.append(f"  2. Click 'Download' to get CSV")
                preprocessing_report.append(f"  3. Click 'Analyze' to continue working with it")
                preprocessing_report.append(f"\n🔗 **File ID**: `{new_file_id}`")
                
                results.append("\n".join(preprocessing_report))
                actions_performed.append(f"preprocessing_executed_{new_file_id[:8]}")
            else:
                # No database access - just report what would be done
                results.append(f"🔧 **Preprocessing Applied** (no database save):\n- Missing: {config['missing']}\n- Scaling: {config['scaling']}\n- Outliers: {config['outlier']}\n- Encoding: {config['encode']}")
                actions_performed.append("preprocessing_dry_run")
                
        except Exception as e:
            results.append(f"⚠️ **Preprocessing Error**: {str(e)}")
            actions_performed.append("preprocessing_failed")
    
    # Intent: Filter
    if 'filter' in query_lower or 'where' in query_lower:
        results.append("🔍 **Filtering**: Use the Analysis tab to filter data based on conditions")
        actions_performed.append("filter_guidance")
    
    # Intent: Correlation / Relationship
    if any(word in query_lower for word in ['correlat', 'relationship', 'relate']):
        num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if len(num_cols) >= 2:
            # Calculate top correlations
            corr_matrix = df[num_cols].corr()
            results.append(f"🔗 **Correlation Analysis**: Found {len(num_cols)} numerical columns. Check the Visualization tab for correlation heatmap.")
        actions_performed.append("correlation_analysis")
    
    if not results:
        return None, []
    
    return "\n\n".join(results), actions_performed


# ---- Agentic AI with Intent Detection ----
def ai_analysis_gemini(df: pd.DataFrame, query: str, model: str = "models/gemini-2.5-flash") -> str:
    """Agentic AI with intent detection and action execution.
    
    Detects user intent and performs actions like:
    - Data summarization
    - Preprocessing recommendations
    - Visualization suggestions
    - Filtering guidance
    """
    if GENAI is None:
        s = "Gemini not configured. Local summary:\n\n"
        s += df.describe(include='all').to_string()
        return s
    
    # First, detect intent and execute actions (pass None for db_session in AI context)
    action_response, actions = detect_intent_and_execute(df, query, file_id=None, db_session=None)
    
    # Build context for AI
    cols = list(df.columns)
    sample = df.head(3).to_dict(orient="records")
    missing = df.isnull().sum().to_dict()
    
    # If actions were performed, include them in the context
    context_addon = ""
    if action_response:
        context_addon = f"\n\nActions Already Performed:\n{action_response}\n"
    
    prompt_text = f"""You are an expert data analyst AI assistant for an EDA (Exploratory Data Analysis) application.

Dataset Context:
- Columns: {cols}
- Shape: {df.shape}
- Missing values: {missing}
- Sample (first 3 rows): {json.dumps(sample, default=str)}

{context_addon}

User Query: {query}

Provide a helpful, actionable response. If the user asks for visualizations, guide them to the Visualization tab. If they ask for preprocessing, guide them to the Preprocessing tab. Be concise and practical."""

    # Try models
    models_to_try = [model, "models/gemini-2.5-flash", "models/gemini-2.0-flash"]
    
    for try_model in models_to_try:
        try:
            print(f"🤖 AI (intent-based) trying model: {try_model}")
            m = GENAI.GenerativeModel(try_model)
            r = m.generate_content(prompt_text)
            
            if hasattr(r, "text"):
                ai_response = r.text
                print(f"✅ Success with {try_model}")
                
                # Combine action results with AI response
                if actions:
                    return f"{action_response}\n\n---\n\n{ai_response}\n\n**Actions Performed**: {', '.join(actions)}"
                return ai_response
                
            elif hasattr(r, "candidates") and len(r.candidates) > 0:
                c = r.candidates[0]
                if hasattr(c, "content") and hasattr(c.content, "parts") and len(c.content.parts) > 0:
                    ai_response = c.content.parts[0].text
                    print(f"✅ Success with {try_model}")
                    if actions:
                        return f"{action_response}\n\n---\n\n{ai_response}\n\n**Actions Performed**: {', '.join(actions)}"
                    return ai_response
                    
        except Exception as e:
            error_msg = str(e)
            print(f"❌ {try_model} failed: {error_msg[:150]}...")
            if "429" in error_msg or "quota" in error_msg.lower():
                continue
            continue
    
    # Fallback: return action results if AI failed
    if action_response:
        return action_response
    
    return f"AI analysis temporarily unavailable.\n\nFallback summary:\n{df.describe(include='all').to_string()}"


# ---- Helper: Save Plots to Database ----
def save_plots_to_db(db_session, file_id: str, plots: List[Tuple[str, Any]], user_id: int = None) -> int:
    """Save a list of plots to the database and return the count saved."""
    if not db_session or not file_id:
        return 0
    
    plots_saved = 0
    for plot_name, fig in plots:
        try:
            # Convert to base64
            if hasattr(fig, 'savefig'):  # Matplotlib
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)
                img_b64 = base64.b64encode(buf.read()).decode()
            else:  # Plotly
                img_bytes = fig.to_image(format="png")
                img_b64 = base64.b64encode(img_bytes).decode()
            
            from .db import PlotHistory
            plot = PlotHistory(
                plot_name=plot_name,
                plot_type="auto",
                plot_base64=img_b64,
                file_id=file_id,
                user_id=user_id
            )
            db_session.add(plot)
            plots_saved += 1
        except Exception as e:
            print(f"❌ Failed to save plot {plot_name}: {e}")
    
    if plots_saved > 0:
        db_session.commit()
    
    return plots_saved


# ---- Smart Autonomous Agentic AI ----
def ai_analysis_gemini_agentic(df: pd.DataFrame, query: str, file_id: str, db_session, user_id: int = None, model: str = "models/gemini-2.5-flash") -> str:
    """
    Truly autonomous agentic AI that understands natural language and automatically executes operations.
    Uses Gemini's intelligence to parse generic requests and make smart decisions.
    Supports Streamlit-style file referencing: "file 0", "file 1" for easy merge operations.
    """
    if GENAI is None:
        s = "Gemini not configured. Local summary:\n\n"
        s += df.describe(include='all').to_string()
        return s
    
    from .db import Dataset, PlotHistory
    
    # Get all available datasets with FULL CONTEXT (columns + sample data) for file referencing
    if user_id:
        all_datasets = db_session.query(Dataset).filter(Dataset.user_id == user_id).order_by(Dataset.upload_time).all()
    else:
        all_datasets = db_session.query(Dataset).order_by(Dataset.upload_time).all()
    
    # Load column info and samples from ALL files for Gemini context (optimized)
    file_details = []
    for idx, ds in enumerate(all_datasets):
        try:
            temp_df = load_dataframe(ds.file_path)
            cols_list = list(temp_df.columns)
            # Only get 1 row sample and limit to 10 columns max for brevity
            sample_row = temp_df.head(1).to_dict(orient='records')[0] if len(temp_df) > 0 else {}
            # Truncate sample to first 10 columns to avoid context overload
            cols_preview = cols_list[:10]
            if len(cols_list) > 10:
                cols_preview.append(f"...+{len(cols_list)-10} more")
            
            file_details.append({
                'index': idx,
                'filename': ds.filename,
                'file_id': ds.file_id,
                'rows': ds.rows,
                'columns': ds.columns,
                'column_names': cols_list,  # Keep full list for processing
                'column_preview': cols_preview,  # Shorter version for display
                'sample_data': sample_row
            })
        except Exception as e:
            # If file can't be loaded, just show basic info
            file_details.append({
                'index': idx,
                'filename': ds.filename,
                'file_id': ds.file_id,
                'rows': ds.rows,
                'columns': ds.columns,
                'column_names': [],
                'column_preview': [],
                'sample_data': {}
            })
    
    # Format file list with detailed context (concise for Gemini)
    file_list_context = "\n".join([
        f"File {f['index']}: {f['filename']} | {f['rows']}×{f['columns']} | Cols: {f['column_preview']}"
        for f in file_details
    ])
    
    # Find current file index
    current_file_idx = next((idx for idx, ds in enumerate(all_datasets) if ds.file_id == file_id), None)
    current_file_info = f"\n🎯 Current active file: File {current_file_idx} ({all_datasets[current_file_idx].filename})" if current_file_idx is not None else ""
    
    # Step 1: Use Gemini to understand the user's intent and data characteristics
    cols = list(df.columns)
    dtypes_str = {col: str(dtype) for col, dtype in df.dtypes.items()}
    missing = df.isnull().sum().to_dict()
    missing_pct = {col: (df[col].isnull().sum() / len(df) * 100) if len(df) > 0 else 0 for col in cols}
    sample = df.head(3).to_dict(orient="records")
    
    # Gather data insights for smart decision-making
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    high_cardinality_cols = [col for col in categorical_cols if df[col].nunique() > 50]
    high_missing_cols = [col for col, pct in missing_pct.items() if pct > 70]
    
    understanding_prompt = f"""You are an autonomous EDA agent. Analyze this request and decide what to do.

AVAILABLE FILES:
{file_list_context}{current_file_info}

CURRENT DATASET:
- Columns: {cols[:15]}{'...' if len(cols) > 15 else ''}
- Shape: {df.shape[0]} rows × {df.shape[1]} columns
- Numeric: {numeric_cols[:10]}{'...' if len(numeric_cols) > 10 else ''}
- Categorical: {categorical_cols[:10]}{'...' if len(categorical_cols) > 10 else ''}
- Missing: {high_missing_cols} (>70%)
- Sample: {json.dumps(sample[:1], default=str)}

USER REQUEST: "{query}"

For MERGE: Check column names from files above. Only suggest columns that EXIST in BOTH files.
For PREPROCESS: Use data characteristics to make smart decisions.
For VISUALIZE: Match plot types to data types.

OPTIONS: ANALYZE | VISUALIZE | PREPROCESS | MERGE | EXPLAIN

For MERGE requests, identify:
- Which file indices to merge (e.g., "file 0 and file 1")
- **IMPORTANT**: Look at the actual column names provided above for EACH file
- Common columns that exist in BOTH files (check the column_names lists carefully!)
- Merge type (inner/left/right/outer) based on context
- Use fuzzy matching only if column values are similar but not exact

For PREPROCESS requests, determine:
- Should we handle missing values? (yes/no) and method (mean/median/knn/drop)
- Should we handle outliers? (yes/no) and method (iqr/zscore/isolation_forest)
- Should we encode categorical? (yes/no) and method (onehot/label/ordinal)
- Should we scale? (yes/no) and method (standard/minmax/robust)
- Which columns to drop? (list high missing or irrelevant columns like ID, Name, Ticket)
- Any other transformations needed?

For VISUALIZE requests:
- Look at numeric vs categorical columns
- Check sample data to understand relationships
- Suggest appropriate plot types based on data characteristics

Respond ONLY with JSON in this format:
{{
  "intent": "ANALYZE|VISUALIZE|PREPROCESS|MERGE|EXPLAIN",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation with reference to actual columns you see",
  "merge_plan": {{
    "file_indices": [0, 1],
    "merge_keys": ["actual_column_that_exists_in_both"],
    "merge_type": "inner|left|right|outer",
    "fuzzy": false
  }},
  "preprocessing_plan": {{
    "handle_missing": true/false,
    "missing_strategy": "mean|median|knn|drop",
    "handle_outliers": true/false,
    "outlier_method": "iqr|zscore|isolation_forest",
    "encode_categorical": true/false,
    "encoding_method": "onehot|label|ordinal",
    "scale_data": true/false,
    "scaling_method": "standard|minmax|robust",
    "drop_columns": ["col1", "col2"],
    "other_transformations": "description"
  }}
}}

Examples:
- "clean my data" → PREPROCESS with smart defaults based on data characteristics
- "merge file 0 and file 1" → MERGE with auto-detected keys
- "combine first two datasets" → MERGE files 0 and 1
- "preprocess appropriately" → PREPROCESS with automatic decisions
- "visualize this" → VISUALIZE with auto plots
- "what's in this dataset?" → ANALYZE
- "fill missing values and encode" → PREPROCESS with specific operations"""

    try:
        # Get Gemini's intelligent understanding
        m = GENAI.GenerativeModel("models/gemini-2.5-flash")
        understanding_response = m.generate_content(understanding_prompt)
        
        if hasattr(understanding_response, "text"):
            response_text = understanding_response.text
        elif hasattr(understanding_response, "candidates") and len(understanding_response.candidates) > 0:
            response_text = understanding_response.candidates[0].content.parts[0].text
        else:
            # Fallback to keyword detection
            return ai_analysis_gemini_agentic_fallback(df, query, file_id, db_session, model)
        
        # Extract JSON from response (handle markdown code blocks)
        import re
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON without code blocks
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Fallback to keyword detection
                return ai_analysis_gemini_agentic_fallback(df, query, file_id, db_session, model)
        
        # Parse the intent
        intent_data = json.loads(json_str)
        intent = intent_data.get("intent", "EXPLAIN")
        reasoning = intent_data.get("reasoning", "")
        
        print(f"🤖 Gemini Intent: {intent} | Confidence: {intent_data.get('confidence', 0)} | Reasoning: {reasoning}")
        
        # Execute based on intent
        if intent == "MERGE":
            # Handle merge operations with Streamlit-style file referencing
            merge_plan = intent_data.get("merge_plan", {})
            file_indices = merge_plan.get("file_indices", [])
            merge_keys = merge_plan.get("merge_keys", [])
            merge_type = merge_plan.get("merge_type", "inner")
            use_fuzzy = merge_plan.get("fuzzy", False)
            
            if len(file_indices) < 2:
                return "❌ **Merge Error:** Need at least 2 files to merge. Example: 'merge file 0 and file 1'"
            
            try:
                # Get the datasets
                left_ds = all_datasets[file_indices[0]]
                right_ds = all_datasets[file_indices[1]]
                
                # Load dataframes
                left_df = load_dataframe(left_ds.file_path)
                right_df = load_dataframe(right_ds.file_path)
                
                # Get detailed column info for both files
                left_detail = next((f for f in file_details if f['index'] == file_indices[0]), None)
                right_detail = next((f for f in file_details if f['index'] == file_indices[1]), None)
                
                # Auto-detect merge keys if not provided or if provided key doesn't exist
                left_cols = set(left_df.columns)
                right_cols = set(right_df.columns)
                
                if not merge_keys or merge_keys[0] not in left_cols or merge_keys[0] not in right_cols:
                    common_cols = list(left_cols & right_cols)
                    
                    if common_cols:
                        merge_keys = common_cols[:1]  # Use first common column
                        print(f"🔍 Auto-detected merge key: {merge_keys[0]} (Common columns: {common_cols})")
                    else:
                        return f"""❌ **No common columns found!**

**File {file_indices[0]} ({left_ds.filename})** columns:
{list(left_df.columns)}

**File {file_indices[1]} ({right_ds.filename})** columns:
{list(right_df.columns)}

These files have no overlapping columns. Please check if you selected the correct files or if they can be merged."""
                
                merge_key = merge_keys[0]
                
                # Validate merge key exists in both dataframes
                if merge_key not in left_cols:
                    return f"❌ **Merge Error:** Column '{merge_key}' not found in File {file_indices[0]} ({left_ds.filename}).\n\nAvailable columns: {list(left_df.columns)}"
                if merge_key not in right_cols:
                    return f"❌ **Merge Error:** Column '{merge_key}' not found in File {file_indices[1]} ({right_ds.filename}).\n\nAvailable columns: {list(right_df.columns)}"
                
                # Perform merge
                if use_fuzzy:
                    # For fuzzy merge, use fuzzywuzzy to match similar values
                    try:
                        from fuzzywuzzy import process
                        # Create mapping for fuzzy matching
                        left_values = left_df[merge_key].unique()
                        right_values = right_df[merge_key].unique()
                        
                        # Map fuzzy matches
                        fuzzy_map = {}
                        for lval in left_values:
                            match, score = process.extractOne(str(lval), [str(x) for x in right_values])
                            if score >= 80:  # 80% similarity threshold
                                fuzzy_map[lval] = match
                        
                        # Create temporary column for merge
                        left_df['_merge_key_tmp'] = left_df[merge_key].map(lambda x: fuzzy_map.get(x, x))
                        right_df['_merge_key_tmp'] = right_df[merge_key]
                        
                        merged_df = pd.merge(left_df, right_df, 
                                           left_on='_merge_key_tmp', 
                                           right_on='_merge_key_tmp', 
                                           how=merge_type)
                        merged_df = merged_df.drop('_merge_key_tmp', axis=1)
                    except ImportError:
                        # Fallback to regular merge if fuzzywuzzy not installed
                        merged_df = pd.merge(left_df, right_df, 
                                           left_on=merge_key, 
                                           right_on=merge_key, 
                                           how=merge_type)
                else:
                    merged_df = pd.merge(left_df, right_df, 
                                       left_on=merge_key, 
                                       right_on=merge_key, 
                                       how=merge_type)
                
                # Save merged dataset
                new_file_id = str(uuid.uuid4())
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"merged_{left_ds.filename.replace('.csv', '')}_{right_ds.filename.replace('.csv', '')}_{timestamp}.csv"
                save_path = os.path.join("uploaded_files", new_filename)
                
                os.makedirs("uploaded_files", exist_ok=True)
                merged_df.to_csv(save_path, index=False)
                
                # Add to database
                from .db import Dataset
                new_dataset = Dataset(
                    file_id=new_file_id,
                    filename=new_filename,
                    file_path=save_path,
                    rows=merged_df.shape[0],
                    columns=merged_df.shape[1],
                    size_bytes=os.path.getsize(save_path)
                )
                db_session.add(new_dataset)
                db_session.commit()
                
                result = f"""✅ **Merge Complete!**

**Files Merged:**
• File {file_indices[0]}: {left_ds.filename} ({left_df.shape[0]} rows)
• File {file_indices[1]}: {right_ds.filename} ({right_df.shape[0]} rows)

**Merge Details:**
• Key: `{merge_key}`
• Type: `{merge_type}`
• Result: {merged_df.shape[0]:,} rows × {merged_df.shape[1]} columns

**New File ID:** `{new_file_id}`
**Download:** [merged_dataset.csv](/api/download/{new_file_id})

🎯 This is now **File {len(all_datasets)}** - you can reference it in future operations!
"""
                return result
                
            except IndexError:
                return f"❌ **Error:** Invalid file indices. Available files: 0 to {len(all_datasets)-1}"
            except Exception as e:
                return f"❌ **Merge Error:** {str(e)}"
        
        elif intent == "ANALYZE":
            # Generate data summary
            summary = f"**Data Analysis Summary:**\n\n"
            summary += f"📊 **Shape:** {df.shape[0]:,} rows × {df.shape[1]} columns\n\n"
            summary += f"📋 **Columns:** {', '.join(cols)}\n\n"
            summary += f"🔢 **Numeric:** {', '.join(numeric_cols) if numeric_cols else 'None'}\n\n"
            summary += f"📝 **Categorical:** {', '.join(categorical_cols) if categorical_cols else 'None'}\n\n"
            summary += f"❓ **Missing Values:** {sum(missing.values()):,} total\n\n"
            
            if high_missing_cols:
                summary += f"⚠️ **High Missing (>70%):** {', '.join(high_missing_cols)}\n\n"
            
            summary += f"**Statistical Summary:**\n```\n{df.describe(include='all').to_string()}\n```"
            return summary
            
        elif intent == "VISUALIZE":
            # Generate and save visualizations
            plots = create_smart_visualizations(df, max_plots=8)
            if plots:
                save_plots_to_db(db_session, file_id, plots, user_id)
                return f"✅ **Generated {len(plots)} visualizations!**\n\n" + \
                       "Plots created:\n" + "\n".join([f"• {title}" for title, _ in plots]) + \
                       "\n\n📥 **Download them from the Visualization Panel or use the 'Download Plots' button!**"
            return "⚠️ Could not generate visualizations for this dataset."
            
        elif intent == "PREPROCESS":
            # Execute intelligent preprocessing
            plan = intent_data.get("preprocessing_plan", {})
            
            # Map plan to actual preprocess_dataset parameters
            missing_strategy = plan.get("missing_strategy", "median")
            outlier_method = plan.get("outlier_method", "iqr")
            encoding_method = plan.get("encoding_method", "onehot")
            scaling_method = plan.get("scaling_method", "standard")
            
            # Build preprocessing config matching actual function signature
            config = {
                "missing": missing_strategy if plan.get("handle_missing", True) else "none",
                "cat_missing": "mode",
                "outlier": outlier_method if plan.get("handle_outliers", True) else "none",
                "outlier_action": "cap",
                "encode": encoding_method if plan.get("encode_categorical", True) else "none",
                "scaling": scaling_method if plan.get("scale_data", True) else "none",
            }
            
            # Drop columns if recommended
            columns_to_drop = plan.get("drop_columns", [])
            if columns_to_drop:
                existing_cols_to_drop = [col for col in columns_to_drop if col in df.columns]
                if existing_cols_to_drop:
                    df = df.drop(columns=existing_cols_to_drop)
                    print(f"🗑️ Dropped columns: {existing_cols_to_drop}")
            
            # Perform preprocessing
            processed_df, actions_taken = preprocess_dataset(df, **config)
            
            if processed_df is not None:
                # Save to database
                new_file_id = str(uuid.uuid4())
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"{file_id}_preprocessed_{timestamp}.csv"
                save_path = os.path.join("uploaded_files", new_filename)
                
                os.makedirs("uploaded_files", exist_ok=True)
                processed_df.to_csv(save_path, index=False)
                
                # Add to database with correct field names
                from .db import Dataset
                new_dataset = Dataset(
                    file_id=new_file_id,
                    filename=new_filename,
                    file_path=save_path,
                    rows=processed_df.shape[0],
                    columns=processed_df.shape[1],
                    size_bytes=os.path.getsize(save_path)
                )
                db_session.add(new_dataset)
                db_session.commit()
                
                result = f"""✅ **Preprocessing Complete!**

**Operations Performed:**
{chr(10).join([f"• {action}" for action in actions_taken])}

**Before:** {df.shape[0]:,} rows × {df.shape[1]} columns
**After:** {processed_df.shape[0]:,} rows × {processed_df.shape[1]} columns

**New File ID:** `{new_file_id}`

📥 **Download the preprocessed dataset from the Preprocess Panel!**"""
                
                return result
            else:
                return "⚠️ Preprocessing failed. Please try with specific parameters."
        
        else:  # EXPLAIN
            # Just provide explanation, no action
            final_prompt = f"""Based on this dataset and user request, provide a helpful explanation:

Dataset: {df.shape[0]} rows × {df.shape[1]} columns
Columns: {cols}
User Query: {query}

Provide a clear, concise response."""
            
            final_response = m.generate_content(final_prompt)
            if hasattr(final_response, "text"):
                return final_response.text
            elif hasattr(final_response, "candidates") and len(final_response.candidates) > 0:
                return final_response.candidates[0].content.parts[0].text
            return "I can help you analyze this dataset. Try asking for specific analysis, visualizations, or preprocessing."
            
    except Exception as e:
        print(f"❌ Autonomous agent error: {str(e)}")
        # Fallback to keyword-based detection
        return ai_analysis_gemini_agentic_fallback(df, query, file_id, db_session, model)


def ai_analysis_gemini_agentic_fallback(df: pd.DataFrame, query: str, file_id: str, db_session, user_id: int = None, model: str = "models/gemini-2.5-flash") -> str:
    """Fallback to keyword-based detection if autonomous mode fails."""
    print("⚠️ Using fallback keyword detection mode")
    
    # Use the original detect_intent_and_execute function
    action_response, actions = detect_intent_and_execute(df, query, file_id=file_id, db_session=db_session, user_id=user_id)
    
    # Build context for AI
    cols = list(df.columns)
    sample = df.head(3).to_dict(orient="records")
    missing = df.isnull().sum().to_dict()
    
    context_addon = ""
    if action_response:
        context_addon = f"\n\nActions Already Performed:\n{action_response}\n"
    
    prompt_text = f"""You are an expert data analyst AI assistant for an EDA (Exploratory Data Analysis) application.

Dataset Context:
- Columns: {cols}
- Shape: {df.shape}
- Missing values: {missing}
- Sample (first 3 rows): {json.dumps(sample, default=str)}

{context_addon}

User Query: {query}

Provide a helpful, actionable response. Be concise and practical."""

    models_to_try = [model, "models/gemini-2.5-flash", "models/gemini-2.0-flash"]
    
    for try_model in models_to_try:
        try:
            m = GENAI.GenerativeModel(try_model)
            r = m.generate_content(prompt_text)
            
            if hasattr(r, "text"):
                ai_response = r.text
                if actions:
                    return f"{action_response}\n\n---\n\n{ai_response}\n\n**Actions Performed**: {', '.join(actions)}"
                return ai_response
                
            elif hasattr(r, "candidates") and len(r.candidates) > 0:
                c = r.candidates[0]
                if hasattr(c, "content") and hasattr(c.content, "parts") and len(c.content.parts) > 0:
                    ai_response = c.content.parts[0].text
                    if actions:
                        return f"{action_response}\n\n---\n\n{ai_response}\n\n**Actions Performed**: {', '.join(actions)}"
                    return ai_response
                    
        except Exception as e:
            continue
    
    if action_response:
        return action_response
    
    return f"AI analysis temporarily unavailable.\n\nFallback summary:\n{df.describe(include='all').to_string()}"
