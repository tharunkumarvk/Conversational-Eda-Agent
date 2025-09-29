# backend/helpers.py
import os
import io
import json
import traceback
from typing import List, Tuple, Optional
from datetime import datetime

import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.ensemble import IsolationForest

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
    load_dotenv()
except Exception:
    pass

# init gemini if available
GENAI = None
def init_genai():
    global GENAI
    if not GENAI_AVAILABLE:
        GENAI = None
        return
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        GENAI = None
        return
    try:
        genai.configure(api_key=key)
        GENAI = genai
    except Exception:
        GENAI = None

init_genai()

# ---- Basic IO / loading ----
def load_dataframe(path: str) -> pd.DataFrame:
    path = str(path)
    if path.lower().endswith(".csv"):
        return pd.read_csv(path)
    if path.lower().endswith((".xls", ".xlsx")):
        return pd.read_excel(path)
    raise ValueError("Unsupported file type: " + path)

# ---- Merge multiple datasets ----
def merge_datasets(dfs: List[pd.DataFrame], on: Optional[str] = None, how: str = "inner") -> pd.DataFrame:
    if not dfs:
        raise ValueError("No dataframes provided")
    if len(dfs) == 1:
        return dfs[0].copy()
    result = dfs[0].copy()
    for nxt in dfs[1:]:
        if on and on in result.columns and on in nxt.columns:
            result = pd.merge(result, nxt, left_on=on, right_on=on, how=how)
        else:
            common = [c for c in result.columns if c in nxt.columns]
            if common:
                result = pd.merge(result, nxt, on=common, how=how)
            else:
                # index concat/merge
                result = pd.merge(result.reset_index(drop=True), nxt.reset_index(drop=True), left_index=True, right_index=True, how=how)
    return result

# ---- Preprocessing ----
def preprocess_dataset(df: pd.DataFrame, missing: str = "mean", scaling: str = "none", outlier: str = "none", encode: str = "none") -> pd.DataFrame:
    d = df.copy()
    num_cols = d.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = d.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    # missing
    if missing == "mean" and num_cols:
        d[num_cols] = d[num_cols].fillna(d[num_cols].mean())
    elif missing == "median" and num_cols:
        d[num_cols] = d[num_cols].fillna(d[num_cols].median())
    elif missing == "drop":
        d = d.dropna()

    # categorical fill (simple mode)
    if encode != "none" and cat_cols:
        # fill categorical missing with mode
        for c in cat_cols:
            if d[c].isnull().any():
                d[c] = d[c].fillna(d[c].mode().iloc[0] if not d[c].mode().empty else "NA")

    # encoding
    if encode == "onehot" and cat_cols:
        d = pd.get_dummies(d, columns=cat_cols, drop_first=False)
    elif encode == "label" and cat_cols:
        for c in cat_cols:
            d[c] = pd.factorize(d[c])[0]

    # scaling
    if scaling == "standard" and num_cols:
        d[num_cols] = StandardScaler().fit_transform(d[num_cols])
    elif scaling == "minmax" and num_cols:
        d[num_cols] = MinMaxScaler().fit_transform(d[num_cols])

    # outlier handling
    if outlier == "zscore" and num_cols:
        z = (d[num_cols] - d[num_cols].mean()) / d[num_cols].std()
        mask = (z.abs() < 3).all(axis=1)
        d = d[mask]
    elif outlier == "isolation" and num_cols:
        iso = IsolationForest(contamination=0.05, random_state=42)
        mask = iso.fit_predict(d[num_cols]) == 1
        d = d[mask]

    return d

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

    if plot_type == "scatter":
        if not x or not y:
            if len(num) >= 2:
                x, y = num[0], num[1]
            else:
                raise ValueError("Need two numeric columns for scatter")
        fig = px.scatter(d, x=x, y=y, color=color, title=f"Scatter: {x} vs {y}")
        return fig

    if plot_type in ("hist", "histogram"):
        if not x:
            x = num[0] if num else d.columns[0]
        fig = px.histogram(d, x=x, nbins=40, title=f"Histogram: {x}")
        return fig

    if plot_type == "line":
        fig = px.line(d, x=x or d.columns[0], y=y or d.columns[1] if len(d.columns) > 1 else d.columns[0], color=color, title="Line plot")
        return fig

    if plot_type in ("bar", "count"):
        fig = px.bar(d, x=x or (cat[0] if cat else d.columns[0]), y=y, color=color, title="Bar plot")
        return fig

    if plot_type == "box":
        fig = px.box(d, x=x, y=y, title="Box plot")
        return fig

    if plot_type == "violin":
        fig = px.violin(d, x=x, y=y, box=True, title="Violin plot")
        return fig

    if plot_type == "heatmap":
        if len(num) < 2:
            raise ValueError("Not enough numeric columns for heatmap")
        fig = px.imshow(d[num].corr().round(2), text_auto=True, title="Heatmap")
        return fig

    if plot_type == "pairplot":
        import seaborn as sns
        ps = d[num].sample(min(200, len(d))) if len(num) >= 2 else d
        g = sns.pairplot(ps)
        return g.fig

    if plot_type == "pie":
        if not x:
            x = cat[0] if cat else d.columns[0]
        fig = px.pie(d, names=x, title="Pie chart")
        return fig

    raise ValueError("Unsupported plot type: " + str(plot_type))

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

# ---- AI / Gemini analysis (planner + insight) ----
def ai_analysis_gemini(df: pd.DataFrame, query: str, model: str = "gemini-2.0-flash-exp") -> str:
    if GENAI is None:
        # fallback local simple summary if no Gemini
        s = "Gemini not configured. Local summary:\n\n"
        s += df.describe(include='all').to_string()
        return s
    # build concise summary to send
    cols = list(df.columns)
    sample = df.head(5).to_dict(orient="records")
    missing = df.isnull().sum().to_dict()
    prompt = {
        "task": "EDA_insights",
        "query": query,
        "columns": cols,
        "sample_rows": sample,
        "missing_counts": missing,
        "notes": "Return concise actionable insights and steps. If instruction requires operations (merge/preprocess/plot), describe them in a JSON actions list."
    }
    prompt_text = "User asks: " + query + "\nDataset meta (columns, sample, missing):\n" + json.dumps(prompt, default=str, indent=2)
    try:
        # try chat.create first
        try:
            resp = GENAI.chat.create(model=model, messages=[{"role":"user","content":prompt_text}])
            # parse candidates
            if hasattr(resp, "candidates") and len(resp.candidates) > 0:
                c = resp.candidates[0]
                # extract text where possible
                if hasattr(c, "content") and len(c.content) > 0:
                    txt = getattr(c.content[0], "text", None)
                    if txt: return txt
                return str(c)
            return str(resp)
        except Exception:
            m = GENAI.GenerativeModel(model)
            r = m.generate_content(prompt_text)
            return getattr(r, "text", str(r))
    except Exception as e:
        return f"Gemini call failed: {e}\n{traceback.format_exc()}"
