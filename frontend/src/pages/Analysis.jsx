// src/pages/Analysis.jsx
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { ArrowLeft, MessageSquare, BarChart2, Settings, Sparkles, GitMerge } from 'lucide-react';
import { api } from '../api/client';
import ChatPanel from '../components/ChatPanel';
import PreprocessPanel from '../components/PreprocessPanel';
import VisualizationPanel from '../components/VisualizationPanel';
import MergePanel from '../components/MergePanel';
import '../styles/Analysis.css';

function Analysis() {
  const { fileId } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');

  const { data: datasetInfo, isLoading, error } = useQuery({
    queryKey: ['dataset', fileId],
    queryFn: async () => {
      const response = await api.getDatasetInfo(fileId);
      return response.data;
    },
  });

  const visualSummaryMutation = useMutation({
    mutationFn: () => api.getVisualSummary(fileId),
  });

  const handleGenerateVisuals = () => {
    visualSummaryMutation.mutate();
  };

  if (isLoading) {
    return (
      <div className="analysis-loading">
        <div className="spinner"></div>
        <p>Loading dataset...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analysis-loading">
        <div className="error-message">
          <h2>Error Loading Dataset</h2>
          <p>{error.response?.data?.detail || error.message || 'Failed to load dataset'}</p>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!datasetInfo) {
    return (
      <div className="analysis-loading">
        <p>No dataset found</p>
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          Back to Dashboard
        </button>
      </div>
    );
  }

  const profile = datasetInfo?.profile || {};

  return (
    <div className="analysis">
      <header className="analysis-header">
        <button className="btn-back" onClick={() => navigate('/')}>
          <ArrowLeft size={20} />
          Back to Dashboard
        </button>
        <h1>{datasetInfo?.filename}</h1>
      </header>

      <div className="analysis-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <BarChart2 size={18} />
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'preprocess' ? 'active' : ''}`}
          onClick={() => setActiveTab('preprocess')}
        >
          <Settings size={18} />
          Preprocess
        </button>
        <button
          className={`tab ${activeTab === 'visualize' ? 'active' : ''}`}
          onClick={() => setActiveTab('visualize')}
        >
          <BarChart2 size={18} />
          Visualize
        </button>
        <button
          className={`tab ${activeTab === 'merge' ? 'active' : ''}`}
          onClick={() => setActiveTab('merge')}
        >
          <GitMerge size={18} />
          Merge
        </button>
        <button
          className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          <MessageSquare size={18} />
          AI Chat
        </button>
      </div>

      <div className="analysis-content">
        {activeTab === 'overview' && (
          <div className="overview-panel">
            <div className="stats-grid">
              <div className="stat-card">
                <h3>Shape</h3>
                <p className="stat-value">{profile.shape?.[0]?.toLocaleString()} × {profile.shape?.[1]}</p>
                <p className="stat-label">Rows × Columns</p>
              </div>
              <div className="stat-card">
                <h3>Data Quality</h3>
                <p className="stat-value">{profile.quality_score?.toFixed(1) || 'N/A'}/100</p>
                <p className="stat-label">Quality Score</p>
              </div>
              <div className="stat-card">
                <h3>Memory Usage</h3>
                <p className="stat-value">{profile.memory_usage_mb?.toFixed(2) || 'N/A'} MB</p>
                <p className="stat-label">Total Size</p>
              </div>
              <div className="stat-card">
                <h3>Missing Values</h3>
                <p className="stat-value">
                  {Object.values(profile.missing_values || {}).reduce((a, b) => a + b, 0)}
                </p>
                <p className="stat-label">Total Missing</p>
              </div>
            </div>

            <div className="details-section">
              <h3>Column Information</h3>
              <div className="table-container">
                <table className="info-table">
                  <thead>
                    <tr>
                      <th>Column</th>
                      <th>Type</th>
                      <th>Missing</th>
                      <th>Missing %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {profile.columns?.map((col) => (
                      <tr key={col}>
                        <td>{col}</td>
                        <td>
                          <span className="type-badge">{profile.dtypes?.[col] || 'unknown'}</span>
                        </td>
                        <td>{profile.missing_values?.[col] || 0}</td>
                        <td>{profile.missing_percentage?.[col]?.toFixed(2) || 0}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="actions-section">
              <button
                className="btn btn-primary btn-large"
                onClick={handleGenerateVisuals}
                disabled={visualSummaryMutation.isPending}
              >
                <Sparkles size={20} />
                {visualSummaryMutation.isPending ? 'Generating...' : 'Generate Visual Summary'}
              </button>
            </div>

            {visualSummaryMutation.isSuccess && (
              <div className="visuals-grid">
                {visualSummaryMutation.data?.data?.plots?.map((plot, idx) => (
                  <div key={idx} className="visual-card">
                    <h4>{plot.name}</h4>
                    <img src={`data:image/png;base64,${plot.image}`} alt={plot.name} />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'preprocess' && <PreprocessPanel fileId={fileId} />}
        {activeTab === 'visualize' && <VisualizationPanel fileId={fileId} />}
        {activeTab === 'merge' && <MergePanel />}
        {activeTab === 'chat' && <ChatPanel fileId={fileId} />}
      </div>
    </div>
  );
}

export default Analysis;
