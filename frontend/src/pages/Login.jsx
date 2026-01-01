import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../api/client';
import '../styles/Login.css';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSuccess = async (credentialResponse) => {
    try {
      console.log('Google login successful, sending to backend...');
      // Send Google token to backend
      const response = await api.googleLogin(credentialResponse.credential);

      const { access_token, user } = response.data;
      console.log('Backend authentication successful:', user.email);

      // Save auth state
      login(access_token, user);

      // Redirect to dashboard
      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      alert(`Login failed: ${errorMsg}`);
    }
  };

  const handleError = (error) => {
    console.error('Google Login Failed:', error);
    if (error?.error === 'invalid_client') {
      alert('Google OAuth Error: Please add http://localhost:5174 to authorized origins in Google Cloud Console');
    } else {
      alert(`Google Login Failed: ${error?.error || 'Unknown error'}`);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>🔍 EDA Agent</h1>
          <p>Intelligent Exploratory Data Analysis</p>
        </div>
        
        <div className="login-content">
          <h2>Welcome!</h2>
          <p>Sign in with your Google account to get started</p>
          
          <div className="google-login-button">
            <GoogleLogin
              onSuccess={handleSuccess}
              onError={handleError}
              useOneTap
              theme="filled_blue"
              size="large"
              text="signin_with"
              shape="rectangular"
            />
          </div>
        </div>

        <div className="login-footer">
          <p>By signing in, you agree to our Terms of Service</p>
          <p className="features">
            ✨ Upload datasets • 📊 Generate visualizations • 🤖 AI-powered insights
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
