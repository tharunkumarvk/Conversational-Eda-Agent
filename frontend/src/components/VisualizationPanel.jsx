// src/components/VisualizationPanel.jsx
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { BarChart, Play, Download, Eye, Trash2 } from 'lucide-react';
import { api } from '../api/client';
import '../styles/VisualizationPanel.css';

function VisualizationPanel({ fileId }) {
  const [plotConfig, setPlotConfig] = useState({
    plot_type: 'scatter',
    x: '',
    y: '',
    color: '',
  });
  const [showSavedPlots, setShowSavedPlots] = useState(false);

  const { data: datasetInfo } = useQuery({
    queryKey: ['dataset', fileId],
    queryFn: async () => {
      const response = await api.getDatasetInfo(fileId);
      return response.data;
    },
  });

  const { data: savedPlots, refetch: refetchPlots } = useQuery({
    queryKey: ['savedPlots', fileId],
    queryFn: async () => {
      const response = await api.getSavedPlots(fileId);
      return response.data;
    },
    enabled: showSavedPlots,
  });

  const plotMutation = useMutation({
    mutationFn: (data) => api.createPlot(data),
  });

  const handleDownloadAllPlots = async () => {
    try {
      const response = await api.downloadAllPlots(fileId);
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `plots_${fileId.substring(0, 8)}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download plots');
    }
  };

  const handleDeleteAllPlots = async () => {
    if (!confirm('Delete all saved plots for this dataset?')) return;
    try {
      await api.deleteSavedPlots(fileId);
      refetchPlots();
      alert('Plots deleted successfully');
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Failed to delete plots');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    plotMutation.mutate({ file_id: fileId, ...plotConfig });
  };

  const columns = datasetInfo?.profile?.columns || [];

  return (
    <div className="visualization-panel">
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label>Plot Type</label>
            <select
              value={plotConfig.plot_type}
              onChange={(e) => setPlotConfig({ ...plotConfig, plot_type: e.target.value })}
            >
              <option value="auto">Auto</option>
              <option value="scatter">Scatter Plot</option>
              <option value="line">Line Chart</option>
              <option value="bar">Bar Chart</option>
              <option value="histogram">Histogram</option>
              <option value="box">Box Plot</option>
              <option value="violin">Violin Plot</option>
              <option value="heatmap">Heatmap</option>
              <option value="pie">Pie Chart</option>
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>X Column</label>
            <select
              value={plotConfig.x}
              onChange={(e) => setPlotConfig({ ...plotConfig, x: e.target.value })}
            >
              <option value="">Select column...</option>
              {columns.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Y Column</label>
            <select
              value={plotConfig.y}
              onChange={(e) => setPlotConfig({ ...plotConfig, y: e.target.value })}
            >
              <option value="">Select column...</option>
              {columns.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Color Column (optional)</label>
            <select
              value={plotConfig.color}
              onChange={(e) => setPlotConfig({ ...plotConfig, color: e.target.value })}
            >
              <option value="">None</option>
              {columns.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button type="submit" className="btn btn-primary btn-large" disabled={plotMutation.isPending}>
          <BarChart size={20} />
          {plotMutation.isPending ? 'Generating...' : 'Generate Plot'}
        </button>
      </form>

      {plotMutation.isSuccess && (
        <div className="plot-result">
          <h3>Generated Plot</h3>
          <img src={`data:image/png;base64,${plotMutation.data?.data?.image}`} alt="Generated plot" />
        </div>
      )}

      {plotMutation.isError && (
        <div className="error-box">
          <strong>Error:</strong> {plotMutation.error.response?.data?.detail || plotMutation.error.message}
        </div>
      )}

      <div className="saved-plots-section" style={{ marginTop: '30px', borderTop: '2px solid #e0e0e0', paddingTop: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h3 style={{ margin: 0 }}>Saved Plots</h3>
          <button 
            type="button"
            className="btn btn-secondary"
            onClick={() => setShowSavedPlots(!showSavedPlots)}
          >
            <Eye size={16} />
            {showSavedPlots ? 'Hide' : 'View'} Saved Plots
          </button>
        </div>

        {showSavedPlots && (
          <div>
            {savedPlots?.count > 0 ? (
              <>
                <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
                  <button className="btn btn-primary" onClick={handleDownloadAllPlots}>
                    <Download size={16} />
                    Download All ({savedPlots.count} plots)
                  </button>
                  <button className="btn" onClick={handleDeleteAllPlots} style={{ background: '#dc3545' }}>
                    <Trash2 size={16} />
                    Delete All
                  </button>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '15px' }}>
                  {savedPlots.plots.map((plot) => (
                    <div key={plot.id} style={{ border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden' }}>
                      <img 
                        src={`data:image/png;base64,${plot.plot_base64}`} 
                        alt={plot.plot_name}
                        style={{ width: '100%', height: '250px', objectFit: 'contain', background: '#f8f9fa', padding: '10px' }}
                      />
                      <div style={{ padding: '10px', borderTop: '1px solid #ddd' }}>
                        <div style={{ fontWeight: 'bold', fontSize: '14px' }}>{plot.plot_name}</div>
                        <div style={{ fontSize: '11px', color: '#666', marginTop: '5px' }}>
                          {plot.plot_type} • {new Date(plot.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: '30px', color: '#666', background: '#f8f9fa', borderRadius: '8px' }}>
                No saved plots yet. Generate some plots using AI chat or the form above!
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default VisualizationPanel;
