// src/pages/Dashboard.jsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Upload, Trash2, BarChart3, Database, FileText, Download, LogOut, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../api/client';
import FileUpload from '../components/FileUpload';
import '../styles/Dashboard.css';

function Dashboard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, logout } = useAuth();
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: async () => {
      const response = await api.listDatasets();
      return response.data;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file) => 
      api.uploadFile(file, (progressEvent) => {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(progress);
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      setUploadProgress(0);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (fileId) => api.deleteDataset(fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
  });

  const handleFileUpload = (files) => {
    if (files.length > 0) {
      uploadMutation.mutate(files[0]);
    }
  };

  const handleDelete = (fileId) => {
    if (window.confirm('Are you sure you want to delete this dataset?')) {
      deleteMutation.mutate(fileId);
    }
  };

  const handleDownload = async (fileId, filename) => {
    try {
      const response = await api.downloadFile(fileId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (date) => {
    return new Date(date).toLocaleString();
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-title">
            <BarChart3 size={32} className="header-icon" />
            <h1>EDA Agent Dashboard</h1>
          </div>
          <p className="header-subtitle">Production-Grade Exploratory Data Analysis Platform</p>
        </div>
        <div className="header-user">
          <div className="user-info">
            {user?.picture && <img src={user.picture} alt={user.name} className="user-avatar" />}
            <div className="user-details">
              <span className="user-name">{user?.name}</span>
              <span className="user-email">{user?.email}</span>
            </div>
          </div>
          <button onClick={() => navigate('/profile')} className="profile-btn" title="Profile">
            <User size={20} />
          </button>
          <button onClick={handleLogout} className="logout-btn" title="Logout">
            <LogOut size={20} />
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <section className="upload-section">
          <h2>
            <Upload size={24} />
            Upload Dataset
          </h2>
          <FileUpload onFilesSelected={handleFileUpload} />
          {uploadMutation.isPending && (
            <div className="upload-progress">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
              </div>
              <span>{uploadProgress}%</span>
            </div>
          )}
          {uploadMutation.isError && (
            <div className="error-message">
              Upload failed: {uploadMutation.error.response?.data?.detail || uploadMutation.error.message}
            </div>
          )}
          {uploadMutation.isSuccess && (
            <div className="success-message">
              File uploaded successfully!
            </div>
          )}
        </section>

        <section className="datasets-section">
          <h2>
            <Database size={24} />
            Your Datasets ({datasets?.length || 0})
          </h2>
          
          {isLoading ? (
            <div className="loading">Loading datasets...</div>
          ) : datasets && datasets.length > 0 ? (
            <div className="datasets-grid">
              {datasets.map((dataset) => (
                <div key={dataset.file_id} className="dataset-card">
                  <div className="dataset-header">
                    <FileText size={20} />
                    <h3>{dataset.filename}</h3>
                  </div>
                  <div className="dataset-info">
                    <div className="info-item">
                      <span className="label">Rows:</span>
                      <span className="value">{dataset.rows?.toLocaleString() || 'N/A'}</span>
                    </div>
                    <div className="info-item">
                      <span className="label">Columns:</span>
                      <span className="value">{dataset.columns || 'N/A'}</span>
                    </div>
                    <div className="info-item">
                      <span className="label">Size:</span>
                      <span className="value">{formatBytes(dataset.size)}</span>
                    </div>
                    <div className="info-item">
                      <span className="label">Uploaded:</span>
                      <span className="value">{formatDate(dataset.uploaded)}</span>
                    </div>
                  </div>
                  <div className="dataset-actions">
                    <button
                      className="btn btn-primary"
                      onClick={() => navigate(`/analysis/${dataset.file_id}`)}
                    >
                      <BarChart3 size={16} />
                      Analyze
                    </button>
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleDownload(dataset.file_id, dataset.filename)}
                    >
                      <Download size={16} />
                      Download
                    </button>
                    <button
                      className="btn btn-danger"
                      onClick={() => handleDelete(dataset.file_id)}
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 size={16} />
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <FileText size={48} />
              <p>No datasets uploaded yet</p>
              <p className="text-muted">Upload a CSV or Excel file to get started</p>
            </div>
          )}
        </section>
      </main>

      <footer className="dashboard-footer">
        <p>EDA Agent v2.0 • Production-Grade Data Analysis Platform</p>
      </footer>
    </div>
  );
}

export default Dashboard;
