// src/components/MergePanel.jsx
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { GitMerge, CheckCircle, AlertCircle, ExternalLink } from 'lucide-react';
import { api } from '../api/client';
import { useNavigate } from 'react-router-dom';
import '../styles/MergePanel.css';

function MergePanel() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [config, setConfig] = useState({
    leftFileId: '',
    rightFileId: '',
    leftOn: '',
    rightOn: '',
    how: 'inner',
    fuzzy: false,
    fuzzyThreshold: 80,
    autoMerge: false,
  });

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: async () => {
      const response = await api.listDatasets();
      return response.data;
    },
  });

  // Fetch columns for left dataset
  const { data: leftDatasetInfo } = useQuery({
    queryKey: ['dataset', config.leftFileId],
    queryFn: async () => {
      const response = await api.getDatasetInfo(config.leftFileId);
      return response.data;
    },
    enabled: !!config.leftFileId,
  });

  // Fetch columns for right dataset
  const { data: rightDatasetInfo } = useQuery({
    queryKey: ['dataset', config.rightFileId],
    queryFn: async () => {
      const response = await api.getDatasetInfo(config.rightFileId);
      return response.data;
    },
    enabled: !!config.rightFileId,
  });

  const mergeMutation = useMutation({
    mutationFn: (data) => api.mergeFiles(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
  });

  const leftColumns = leftDatasetInfo?.profile?.columns || [];
  const rightColumns = rightDatasetInfo?.profile?.columns || [];

  // Auto-detect common columns for automatic merge
  const findCommonColumns = () => {
    if (leftColumns.length === 0 || rightColumns.length === 0) return [];
    return leftColumns.filter(col => rightColumns.includes(col));
  };

  // Auto-detect best matching columns using fuzzy matching
  const findBestMatchingColumns = () => {
    if (leftColumns.length === 0 || rightColumns.length === 0) return { leftCol: '', rightCol: '' };
    
    const commonCols = findCommonColumns();
    if (commonCols.length > 0) {
      // Prefer columns with 'id' in the name
      const idCol = commonCols.find(col => col.toLowerCase().includes('id'));
      return { leftCol: idCol || commonCols[0], rightCol: idCol || commonCols[0] };
    }
    
    // Look for similar column names
    const idColLeft = leftColumns.find(col => col.toLowerCase().includes('id'));
    const idColRight = rightColumns.find(col => col.toLowerCase().includes('id'));
    
    if (idColLeft && idColRight) {
      return { leftCol: idColLeft, rightCol: idColRight };
    }
    
    return { leftCol: leftColumns[0] || '', rightCol: rightColumns[0] || '' };
  };

  const handleAutoMerge = () => {
    const { leftCol, rightCol } = findBestMatchingColumns();
    setConfig({
      ...config,
      leftOn: leftCol,
      rightOn: rightCol,
      autoMerge: true,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (config.autoMerge) {
      const { leftCol, rightCol } = findBestMatchingColumns();
      mergeMutation.mutate({
        file_ids: [config.leftFileId, config.rightFileId],
        left_on: leftCol,
        right_on: rightCol,
        how: config.how,
        fuzzy: false,
        fuzzy_threshold: config.fuzzyThreshold,
      });
    } else {
      mergeMutation.mutate({
        file_ids: [config.leftFileId, config.rightFileId],
        left_on: config.leftOn,
        right_on: config.rightOn,
        how: config.how,
        fuzzy: config.fuzzy,
        fuzzy_threshold: config.fuzzyThreshold,
      });
    }
  };

  const availableDatasets = datasets || [];
  const commonColumns = findCommonColumns();

  return (
    <div className="merge-panel streamlit-container">
      <div className="tool-card">
        <h3 className="section-title">
          <GitMerge size={24} />
          Merge Datasets
        </h3>

        <form onSubmit={handleSubmit}>
          <div className="form-section">
            <h4 className="subsection-title">Select Datasets</h4>
            <div className="form-row">
              <div className="form-group">
                <label>Left Dataset</label>
                <select
                  className="streamlit-select"
                  value={config.leftFileId}
                  onChange={(e) => setConfig({ ...config, leftFileId: e.target.value })}
                  required
                >
                  <option value="">Select dataset...</option>
                  {availableDatasets.map((ds) => (
                    <option key={ds.file_id} value={ds.file_id}>
                      {ds.filename} ({ds.rows} rows × {ds.columns} cols)
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Right Dataset</label>
                <select
                  className="streamlit-select"
                  value={config.rightFileId}
                  onChange={(e) => setConfig({ ...config, rightFileId: e.target.value })}
                  required
                >
                  <option value="">Select dataset...</option>
                  {availableDatasets.map((ds) => (
                    <option key={ds.file_id} value={ds.file_id}>
                      {ds.filename} ({ds.rows} rows × {ds.columns} cols)
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="form-section">
            <h4 className="subsection-title">Merge Configuration</h4>
            
            <div className="checkbox-group" style={{ marginBottom: '1.5rem' }}>
              <label>
                <input
                  type="checkbox"
                  checked={config.autoMerge}
                  onChange={(e) => {
                    const isAuto = e.target.checked;
                    setConfig({ ...config, autoMerge: isAuto });
                    if (isAuto) {
                      handleAutoMerge();
                    }
                  }}
                />
                🤖 Auto-Detect Merge Columns (Smart Merge)
              </label>
            </div>

            {commonColumns.length > 0 && !config.autoMerge && (
              <div className="info-box" style={{ 
                background: '#e7f3ff', 
                padding: '1rem', 
                borderRadius: '8px', 
                marginBottom: '1rem',
                border: '1px solid #b3d9ff'
              }}>
                <strong>💡 Common columns found:</strong> {commonColumns.join(', ')}
              </div>
            )}

            {!config.autoMerge && (
              <div className="form-row">
                <div className="form-group">
                  <label>Left Column</label>
                  <select
                    className="streamlit-select"
                    value={config.leftOn}
                    onChange={(e) => setConfig({ ...config, leftOn: e.target.value })}
                    required
                    disabled={!config.leftFileId}
                  >
                    <option value="">Select column...</option>
                    {leftColumns.map((col) => (
                      <option key={col} value={col}>
                        {col}
                      </option>
                    ))}
                  </select>
                  {!config.leftFileId && (
                    <small className="hint-text">Select left dataset first</small>
                  )}
                </div>

                <div className="form-group">
                  <label>Right Column</label>
                  <select
                    className="streamlit-select"
                    value={config.rightOn}
                    onChange={(e) => setConfig({ ...config, rightOn: e.target.value })}
                    required
                    disabled={!config.rightFileId}
                  >
                    <option value="">Select column...</option>
                    {rightColumns.map((col) => (
                      <option key={col} value={col}>
                        {col}
                      </option>
                    ))}
                  </select>
                  {!config.rightFileId && (
                    <small className="hint-text">Select right dataset first</small>
                  )}
                </div>

                <div className="form-group">
                  <label>Join Type</label>
                  <select
                    className="streamlit-select"
                    value={config.how}
                    onChange={(e) => setConfig({ ...config, how: e.target.value })}
                  >
                    <option value="inner">Inner Join</option>
                    <option value="left">Left Join</option>
                    <option value="right">Right Join</option>
                    <option value="outer">Outer Join</option>
                  </select>
                </div>
              </div>
            )}

            {config.autoMerge && (
              <div className="auto-merge-info" style={{
                background: '#f0f9ff',
                padding: '1.5rem',
                borderRadius: '10px',
                border: '2px solid #0ea5e9',
                marginBottom: '1rem'
              }}>
                <h5 style={{ margin: '0 0 0.75rem 0', color: '#0369a1' }}>
                  🤖 Smart Merge Active
                </h5>
                {(() => {
                  const { leftCol, rightCol } = findBestMatchingColumns();
                  return (
                    <div>
                      <p style={{ margin: '0 0 0.5rem 0' }}>
                        <strong>Detected merge columns:</strong>
                      </p>
                      <ul style={{ margin: '0', paddingLeft: '1.5rem' }}>
                        <li>Left: <strong>{leftCol || 'N/A'}</strong></li>
                        <li>Right: <strong>{rightCol || 'N/A'}</strong></li>
                        <li>Join Type: <strong>{config.how}</strong></li>
                      </ul>
                      {commonColumns.length > 0 && (
                        <p style={{ margin: '0.75rem 0 0 0', fontSize: '0.875rem', color: '#0369a1' }}>
                          ✓ Common columns found: {commonColumns.join(', ')}
                        </p>
                      )}
                    </div>
                  );
                })()}
              </div>
            )}
          </div>

          <div className="form-section">
            <h4 className="subsection-title">Advanced Options</h4>
            
            {!config.autoMerge && (
              <>
                <div className="checkbox-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={config.fuzzy}
                      onChange={(e) => setConfig({ ...config, fuzzy: e.target.checked })}
                    />
                    Enable Fuzzy Matching
                  </label>
                </div>

                {config.fuzzy && (
                  <div className="form-group">
                    <label>Fuzzy Matching Threshold: {config.fuzzyThreshold}%</label>
                    <input
                      type="range"
                      className="slider"
                      min="50"
                      max="100"
                      value={config.fuzzyThreshold}
                      onChange={(e) => setConfig({ ...config, fuzzyThreshold: parseInt(e.target.value) })}
                    />
                    <small className="hint-text">
                      Higher values = stricter matching (80-90 recommended)
                    </small>
                  </div>
                )}
              </>
            )}

            {config.autoMerge && (
              <div className="form-group">
                <label>Join Type for Auto-Merge</label>
                <select
                  className="streamlit-select"
                  value={config.how}
                  onChange={(e) => setConfig({ ...config, how: e.target.value })}
                >
                  <option value="inner">Inner Join (only matching rows)</option>
                  <option value="left">Left Join (all left rows)</option>
                  <option value="right">Right Join (all right rows)</option>
                  <option value="outer">Outer Join (all rows)</option>
                </select>
              </div>
            )}
          </div>

          <button
            type="submit"
            className="streamlit-button"
            disabled={mergeMutation.isPending}
          >
            {mergeMutation.isPending ? (
              <>
                <div className="spinner-small"></div>
                Merging...
              </>
            ) : (
              <>
                <GitMerge size={20} />
                Merge Datasets
              </>
            )}
          </button>
        </form>

        {mergeMutation.isSuccess && (
          <div className="success-box streamlit-alert">
            <CheckCircle size={24} style={{ flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <strong style={{ fontSize: '1.125rem' }}>✅ Merge Successful!</strong>
              <div style={{ marginTop: '0.75rem' }}>
                <p style={{ margin: '0 0 0.5rem 0', fontSize: '1rem' }}>
                  <strong>Dataset:</strong> {mergeMutation.data?.data?.filename || 'merged_data.csv'}
                </p>
                <div style={{ 
                  display: 'flex', 
                  gap: '1.5rem', 
                  margin: '0.75rem 0',
                  padding: '0.75rem',
                  background: 'rgba(21, 87, 36, 0.1)',
                  borderRadius: '8px'
                }}>
                  <div>
                    <strong>Rows:</strong> <span style={{ fontSize: '1.25rem', color: '#155724' }}>
                      {mergeMutation.data?.data?.rows?.toLocaleString() || 0}
                    </span>
                  </div>
                  <div>
                    <strong>Columns:</strong> <span style={{ fontSize: '1.25rem', color: '#155724' }}>
                      {mergeMutation.data?.data?.columns || 0}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => navigate(`/analysis/${mergeMutation.data?.data?.file_id}`)}
                  style={{
                    background: 'linear-gradient(135deg, #155724 0%, #1e7e34 100%)',
                    color: 'white',
                    border: 'none',
                    padding: '0.625rem 1.25rem',
                    borderRadius: '8px',
                    fontSize: '0.9375rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    marginTop: '0.5rem',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                  onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                >
                  <ExternalLink size={18} />
                  View Merged Dataset
                </button>
              </div>
            </div>
          </div>
        )}

        {mergeMutation.isError && (
          <div className="error-box streamlit-alert">
            <AlertCircle size={20} />
            <div>
              <strong>❌ Error:</strong>
              <p>{mergeMutation.error.response?.data?.detail || mergeMutation.error.message}</p>
            </div>
          </div>
        )}
      </div>

      <div className="merge-info-card">
        <h4>📚 Merge Types Explained</h4>
        <ul>
          <li><strong>Inner Join:</strong> Only rows with matching keys in both datasets</li>
          <li><strong>Left Join:</strong> All rows from left dataset + matching rows from right</li>
          <li><strong>Right Join:</strong> All rows from right dataset + matching rows from left</li>
          <li><strong>Outer Join:</strong> All rows from both datasets</li>
        </ul>
        
        <h4>🤖 Smart Auto-Merge</h4>
        <p>
          Enable Auto-Merge to automatically detect the best columns to merge on. The algorithm:
        </p>
        <ul>
          <li>First looks for <strong>common column names</strong> (exact matches)</li>
          <li>Prioritizes columns with <strong>"id"</strong> in their name</li>
          <li>Falls back to the first available columns if no ID columns found</li>
        </ul>
        
        <h4>🔍 Fuzzy Matching</h4>
        <p>
          Enable fuzzy matching when column values are similar but not exact (e.g., "John Smith" vs "J. Smith"). 
          Uses intelligent string matching algorithms. Not available with Auto-Merge.
        </p>
      </div>
    </div>
  );
}

export default MergePanel;
