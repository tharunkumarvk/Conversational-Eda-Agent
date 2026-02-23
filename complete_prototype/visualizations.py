"""
Visualization Module  
Creates interactive plots using Plotly
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import List, Optional


def create_distribution_plot(df: pd.DataFrame, column: str):
    """Create distribution plot for numerical column"""
    if df[column].dtype in [np.number, 'int64', 'float64']:
        fig = px.histogram(df, x=column, nbins=30, title=f'Distribution of {column}',
                          marginal="box", color_discrete_sequence=['#8B5CF6'])
        fig.update_layout(template='plotly_dark', showlegend=False)
        return fig
    else:
        value_counts = df[column].value_counts().head(20)
        fig = px.bar(x=value_counts.index, y=value_counts.values, 
                    title=f'Distribution of {column}',
                    labels={'x': column, 'y': 'Count'},
                    color_discrete_sequence=['#8B5CF6'])
        fig.update_layout(template='plotly_dark')
        return fig


def create_correlation_heatmap(df: pd.DataFrame, columns: List[str] = None):
    """Create correlation heatmap"""
    numeric_df = df.select_dtypes(include=[np.number])
    if columns:
        numeric_df = numeric_df[columns]
    
    if numeric_df.empty:
        return None
    
    corr = numeric_df.corr()
    fig = px.imshow(corr, text_auto='.2f', aspect='auto',
                    title='Correlation Heatmap',
                    color_continuous_scale='RdBu_r',
                    zmin=-1, zmax=1)
    fig.update_layout(template='plotly_dark')
    return fig


def create_scatter_plot(df: pd.DataFrame, x_col: str, y_col: str, color_col: str = None):
    """Create scatter plot"""
    fig = px.scatter(df, x=x_col, y=y_col, color=color_col,
                    title=f'{y_col} vs {x_col}',
                    color_discrete_sequence=px.colors.qualitative.Vivid,
                    hover_data=df.columns)
    fig.update_layout(template='plotly_dark')
    fig.update_traces(marker=dict(size=8, line=dict(width=0.5, color='white')))
    return fig


def create_box_plot(df: pd.DataFrame, column: str, group_by: str = None):
    """Create box plot"""
    if group_by:
        fig = px.box(df, x=group_by, y=column, 
                    title=f'{column} by {group_by}',
                    color=group_by,
                    color_discrete_sequence=px.colors.qualitative.Vivid)
    else:
        fig = px.box(df, y=column, title=f'Box Plot: {column}',
                    color_discrete_sequence=['#8B5CF6'])
    
    fig.update_layout(template='plotly_dark')
    return fig


def create_line_plot(df: pd.DataFrame, x_col: str, y_cols: List[str]):
    """Create line plot"""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Vivid
    for i, y_col in enumerate(y_cols):
        fig.add_trace(go.Scatter(x=df[x_col], y=df[y_col], 
                                name=y_col, mode='lines+markers',
                                line=dict(color=colors[i % len(colors)], width=2)))
    
    fig.update_layout(title=f'Line Plot: {", ".join(y_cols)} vs {x_col}',
                     xaxis_title=x_col, yaxis_title='Value',
                     template='plotly_dark', hovermode='x unified')
    return fig


def create_pie_chart(df: pd.DataFrame, column: str, top_n: int = 10):
    """Create pie chart"""
    value_counts = df[column].value_counts().head(top_n)
    fig = px.pie(values=value_counts.values, names=value_counts.index,
                title=f'Distribution: {column} (Top {top_n})',
                color_discrete_sequence=px.colors.qualitative.Vivid)
    fig.update_layout(template='plotly_dark')
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig


def create_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, orientation: str = 'v'):
    """Create bar chart"""
    if orientation == 'h':
        fig = px.bar(df, y=x_col, x=y_col, orientation='h',
                    title=f'{y_col} by {x_col}',
                    color_discrete_sequence=['#8B5CF6'])
    else:
        fig = px.bar(df, x=x_col, y=y_col,
                    title=f'{y_col} by {x_col}',
                    color_discrete_sequence=['#8B5CF6'])
    
    fig.update_layout(template='plotly_dark')
    return fig


def create_3d_scatter(df: pd.DataFrame, x_col: str, y_col: str, z_col: str, color_col: str = None):
    """Create 3D scatter plot"""
    fig = px.scatter_3d(df, x=x_col, y=y_col, z=z_col, color=color_col,
                       title=f'3D Scatter: {x_col}, {y_col}, {z_col}',
                       color_discrete_sequence=px.colors.qualitative.Vivid)
    fig.update_layout(template='plotly_dark',
                     scene=dict(xaxis_title=x_col, yaxis_title=y_col, zaxis_title=z_col))
    return fig


def create_missing_data_plot(df: pd.DataFrame):
    """Visualize missing data"""
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=True)
    
    if missing.empty:
        return None
    
    fig = px.bar(x=missing.values, y=missing.index, orientation='h',
                title='Missing Values by Column',
                labels={'x': 'Count', 'y': 'Column'},
                color_discrete_sequence=['#EC4899'])
    fig.update_layout(template='plotly_dark', height=max(400, len(missing) * 30))
    return fig


def create_summary_stats_table(df: pd.DataFrame):
    """Create summary statistics table"""
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return None
    
    stats = numeric_df.describe().T
    stats['missing'] = df.isnull().sum()
    stats['dtype'] = df.dtypes
    
    fig = go.Figure(data=[go.Table(
        header=dict(values=['Column'] + list(stats.columns),
                   fill_color='#1E1E2E',
                   font=dict(color='white', size=12),
                   align='left'),
        cells=dict(values=[stats.index] + [stats[col] for col in stats.columns],
                  fill_color='#0E1117',
                  font=dict(color='white'),
                  align='left',
                  format=[None] + ['.2f' if col != 'dtype' else None for col in stats.columns]))
    ])
    
    fig.update_layout(title='Summary Statistics', template='plotly_dark', height=min(600, len(stats) * 40 + 100))
    return fig


def create_multi_histogram(df: pd.DataFrame, columns: List[str], bins: int = 20):
    """Create multiple histograms in subplots"""
    n_cols = min(3, len(columns))
    n_rows = (len(columns) + n_cols - 1) // n_cols
    
    fig = make_subplots(rows=n_rows, cols=n_cols, 
                       subplot_titles=columns,
                       vertical_spacing=0.1,
                       horizontal_spacing=0.1)
    
    colors = px.colors.qualitative.Vivid
    for i, col in enumerate(columns):
        row = i // n_cols + 1
        col_idx = i % n_cols + 1
        
        fig.add_trace(
            go.Histogram(x=df[col], nbinsx=bins, name=col,
                        marker_color=colors[i % len(colors)],
                        showlegend=False),
            row=row, col=col_idx
        )
    
    fig.update_layout(height=300*n_rows, title_text="Distribution Analysis",
                     template='plotly_dark')
    return fig
