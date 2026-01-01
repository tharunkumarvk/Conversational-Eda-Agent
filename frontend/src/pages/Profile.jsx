import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import '../styles/Profile.css';

function Profile() {
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchProfileData();
  }, []);

  const fetchProfileData = async () => {
    try {
      setLoading(true);
      const response = await api.getProfileStats();
      setProfileData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching profile:', err);
      setError('Failed to load profile data');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="profile-container">
        <div className="loading">Loading profile...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="profile-container">
        <div className="error">{error}</div>
      </div>
    );
  }

  const { user, statistics, recent_activity } = profileData;

  return (
    <div className="profile-container">
      <div className="profile-header">
        <img src={user.picture} alt={user.name} className="profile-picture" />
        <div className="profile-info">
          <h1>{user.name}</h1>
          <p className="email">{user.email}</p>
          <p className="member-since">Member since: {formatDate(user.member_since)}</p>
          <p className="last-login">Last login: {formatDate(user.last_login)}</p>
        </div>
      </div>

      <div className="statistics-section">
        <h2>Statistics</h2>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-number">{statistics.total_datasets}</div>
            <div className="stat-label">Datasets Uploaded</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{statistics.total_chats}</div>
            <div className="stat-label">AI Conversations</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{statistics.total_plots}</div>
            <div className="stat-label">Plots Generated</div>
          </div>
        </div>
      </div>

      <div className="activity-section">
        <h2>Recent Activity</h2>
        
        <div className="activity-category">
          <h3>Recent Datasets</h3>
          {recent_activity.datasets.length > 0 ? (
            <div className="activity-list">
              {recent_activity.datasets.map((dataset) => (
                <div 
                  key={dataset.file_id} 
                  className="activity-item"
                  onClick={() => navigate(`/analysis/${dataset.file_id}`)}
                >
                  <div className="activity-title">{dataset.filename}</div>
                  <div className="activity-details">
                    {dataset.rows} rows × {dataset.columns} columns
                  </div>
                  <div className="activity-time">{formatDate(dataset.upload_time)}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-activity">No datasets uploaded yet</p>
          )}
        </div>

        <div className="activity-category">
          <h3>Recent Chats</h3>
          {recent_activity.chats.length > 0 ? (
            <div className="activity-list">
              {recent_activity.chats.map((chat, index) => (
                <div key={index} className="activity-item">
                  <div className="activity-title">{chat.query}</div>
                  <div className="activity-time">{formatDate(chat.timestamp)}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-activity">No chat history yet</p>
          )}
        </div>

        <div className="activity-category">
          <h3>Recent Plots</h3>
          {recent_activity.plots.length > 0 ? (
            <div className="activity-list">
              {recent_activity.plots.map((plot, index) => (
                <div key={index} className="activity-item">
                  <div className="activity-title">{plot.plot_name}</div>
                  <div className="activity-details">Type: {plot.plot_type}</div>
                  <div className="activity-time">{formatDate(plot.timestamp)}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-activity">No plots generated yet</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Profile;