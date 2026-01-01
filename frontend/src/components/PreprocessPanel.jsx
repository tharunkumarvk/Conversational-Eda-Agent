// src/components/PreprocessPanel.jsx
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, CheckCircle, Settings, Download } from 'lucide-react';
import { api } from '../api/client';
import '../styles/PreprocessPanel.css';

function PreprocessPanel({ fileId }) {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState({
    missing: 'mean',
    cat_missing: 'mode',
    scaling: 'none',
    outlier: 'none',
    outlier_action: 'cap',
    encode: 'none',
    reduce_dims: false,
    red_method: 'pca',
    n_components: 2,
    feature_selection: false,
    sel_method: 'variance',
  });

  const [showAdvanced, setShowAdvanced] = useState(false);

  const preprocessMutation = useMutation({
    mutationFn: (data) => api.preprocessFile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    preprocessMutation.mutate({ file_id: fileId, ...config });
  };

  return (
    <div className="preprocess-panel streamlit-container">
      <div className="tool-card">
        <h3 className="section-title">
          <Settings size={24} />
          Data Preprocessing Configuration
        </h3>
        
        <form onSubmit={handleSubmit}>
          {/* Basic Options */}
          <div className="form-section">
            <h4 className="subsection-title">Missing Values</h4>
            <div className="form-row">
              <div className="form-group">
                <label>Numeric Strategy</label>
                <select value={config.missing} onChange={(e) => setConfig({ ...config, missing: e.target.value })} className="streamlit-select">
                  <option value="mean">Mean Imputation</option>
                  <option value="median">Median Imputation</option>
                  <option value="knn">KNN Imputation</option>
                  <option value="iterative">Iterative (MICE)</option>
                  <option value="drop">Drop Missing Rows</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Categorical Strategy</label>
                <select value={config.cat_missing} onChange={(e) => setConfig({ ...config, cat_missing: e.target.value })} className="streamlit-select">
                  <option value="mode">Mode (Most Frequent)</option>
                  <option value="constant">Constant (Unknown)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="form-section">
            <h4 className="subsection-title">Outlier Handling</h4>
            <div className="form-row">
              <div className="form-group">
                <label>Detection Method</label>
                <select value={config.outlier} onChange={(e) => setConfig({ ...config, outlier: e.target.value })} className="streamlit-select">
                  <option value="none">None</option>
                  <option value="iqr">IQR Method</option>
                  <option value="zscore">Z-Score (±3σ)</option>
                  <option value="isolation">Isolation Forest</option>
                </select>
              </div>
              
              {config.outlier !== 'none' && (
                <div className="form-group">
                  <label>Action</label>
                  <select value={config.outlier_action} onChange={(e) => setConfig({ ...config, outlier_action: e.target.value })} className="streamlit-select">
                    <option value="cap">Cap (Winsorize)</option>
                    <option value="remove">Remove Rows</option>
                    <option value="transform">Power Transform</option>
                  </select>
                </div>
              )}
            </div>
          </div>

          <div className="form-section">
            <h4 className="subsection-title">Feature Engineering</h4>
            <div className="form-row">
              <div className="form-group">
                <label>Scaling Method</label>
                <select value={config.scaling} onChange={(e) => setConfig({ ...config, scaling: e.target.value })} className="streamlit-select">
                  <option value="none">None</option>
                  <option value="standard">Standard (Z-Score)</option>
                  <option value="minmax">Min-Max [0,1]</option>
                  <option value="robust">Robust (Median/IQR)</option>
                </select>
              </div>

              <div className="form-group">
                <label>Categorical Encoding</label>
                <select value={config.encode} onChange={(e) => setConfig({ ...config, encode: e.target.value })} className="streamlit-select">
                  <option value="none">None</option>
                  <option value="onehot">One-Hot Encoding</option>
                  <option value="label">Label Encoding</option>
                  <option value="ordinal">Ordinal Encoding</option>
                  <option value="binary">Binary Encoding</option>
                  <option value="frequency">Frequency Encoding</option>
                </select>
              </div>
            </div>
          </div>

          {/* Advanced Options */}
          <div className="advanced-toggle">
            <button 
              type="button" 
              className="btn-link" 
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              {showAdvanced ? '▼' : '▶'} Advanced Options
            </button>
          </div>

          {showAdvanced && (
            <>
              <div className="form-section">
                <h4 className="subsection-title">Dimensionality Reduction</h4>
                <div className="form-row">
                  <div className="form-group checkbox-group">
                    <label>
                      <input 
                        type="checkbox" 
                        checked={config.reduce_dims}
                        onChange={(e) => setConfig({ ...config, reduce_dims: e.target.checked })}
                      />
                      Enable Dimensionality Reduction
                    </label>
                  </div>
                </div>
                
                {config.reduce_dims && (
                  <div className="form-row">
                    <div className="form-group">
                      <label>Method</label>
                      <select value={config.red_method} onChange={(e) => setConfig({ ...config, red_method: e.target.value })} className="streamlit-select">
                        <option value="pca">PCA (Principal Component Analysis)</option>
                        <option value="tsne">t-SNE (t-Distributed Stochastic Neighbor Embedding)</option>
                        <option value="svd">SVD (Singular Value Decomposition)</option>
                        <option value="lda">LDA (Linear Discriminant Analysis)</option>
                      </select>
                    </div>
                    
                    <div className="form-group">
                      <label>Components: {config.n_components}</label>
                      <input 
                        type="range" 
                        min="1" 
                        max="20" 
                        value={config.n_components}
                        onChange={(e) => setConfig({ ...config, n_components: parseInt(e.target.value) })}
                        className="slider"
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="form-section">
                <h4 className="subsection-title">Feature Selection</h4>
                <div className="form-row">
                  <div className="form-group checkbox-group">
                    <label>
                      <input 
                        type="checkbox" 
                        checked={config.feature_selection}
                        onChange={(e) => setConfig({ ...config, feature_selection: e.target.checked })}
                      />
                      Enable Feature Selection
                    </label>
                  </div>
                </div>
                
                {config.feature_selection && (
                  <div className="form-row">
                    <div className="form-group">
                      <label>Selection Method</label>
                      <select value={config.sel_method} onChange={(e) => setConfig({ ...config, sel_method: e.target.value })} className="streamlit-select">
                        <option value="variance">Variance Threshold</option>
                        <option value="kbest">K-Best (Chi-squared)</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          <button type="submit" className="btn btn-primary btn-large streamlit-button" disabled={preprocessMutation.isPending}>
            <Play size={20} />
            {preprocessMutation.isPending ? 'Processing...' : 'Apply Preprocessing'}
          </button>
        </form>

        {preprocessMutation.isSuccess && (
          <div className="success-box streamlit-alert">
            <CheckCircle size={20} />
            <div style={{ flex: 1 }}>
              <strong>✅ Preprocessing completed!</strong>
              <p>New file created: <strong>{preprocessMutation.data?.data?.filename}</strong></p>
              <p>Original: {preprocessMutation.data?.data?.original_shape?.[0]} × {preprocessMutation.data?.data?.original_shape?.[1]} → 
                 Processed: {preprocessMutation.data?.data?.processed_shape?.[0]} × {preprocessMutation.data?.data?.processed_shape?.[1]}</p>
            </div>
            <button 
              className="btn btn-secondary"
              onClick={async () => {
                try {
                  const response = await api.downloadFile(preprocessMutation.data?.data?.new_file_id);
                  const blob = new Blob([response.data]);
                  const url = window.URL.createObjectURL(blob);
                  const link = document.createElement('a');
                  link.href = url;
                  link.download = preprocessMutation.data?.data?.filename || 'preprocessed_data.csv';
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                  window.URL.revokeObjectURL(url);
                } catch (error) {
                  console.error('Download failed:', error);
                  alert('Failed to download file');
                }
              }}
            >
              <Download size={16} />
              Download
            </button>
          </div>
        )}

        {preprocessMutation.isError && (
          <div className="error-box streamlit-alert">
            <strong>❌ Error:</strong> {preprocessMutation.error.response?.data?.detail || preprocessMutation.error.message}
          </div>
        )}
      </div>
    </div>
  );
}

export default PreprocessPanel;
