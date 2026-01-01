# 🚀 EDA Agent - Production-Grade Platform

A modern, production-ready Exploratory Data Analysis platform with AI capabilities, featuring a FastAPI backend and React frontend.

## 🌟 Features

### Backend (FastAPI)
- ✅ Production-grade RESTful API
- ✅ Rate limiting and security
- ✅ Comprehensive logging
- ✅ Database persistence (SQLite)
- ✅ File validation and error handling
- ✅ AI-powered analysis with Google Gemini
- ✅ Advanced data preprocessing
- ✅ Automatic visualization generation

### Frontend (React + Vite)
- ✅ Modern, responsive UI
- ✅ Real-time data upload with progress
- ✅ Interactive data analysis dashboard
- ✅ AI chatbot for dataset queries
- ✅ Visual preprocessing tools
- ✅ Custom plot generator
- ✅ File management system

## 📋 Prerequisites

- Python 3.8+
- Node.js 20.17+ (or 20.19+/22.12+ for full compatibility)
- pip
- npm

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd minimal-eda-tarp
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables (already configured)
# The .env file contains your Google API key

# Run the backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/api/docs`

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (already done)
npm install

# Run the development server
npm run dev
```

The frontend will be available at: `http://localhost:5173`

## 🎯 Usage

### Upload a Dataset
1. Navigate to the dashboard
2. Drag & drop or click to upload CSV/Excel files
3. View uploaded datasets with metadata

### Analyze Data
1. Click "Analyze" on any dataset
2. View data quality metrics and statistics
3. Switch between tabs:
   - **Overview**: Dataset summary and quality scores
   - **Preprocess**: Apply transformations (scaling, encoding, outlier removal)
   - **Visualize**: Generate custom plots
   - **AI Chat**: Ask questions about your data

### Preprocessing Options
- **Missing Values**: Mean, Median, Mode, KNN, Iterative imputation, or Drop
- **Scaling**: Standard, MinMax, or Robust scaling
- **Outlier Handling**: Z-Score, IQR, or Isolation Forest
- **Encoding**: One-Hot, Label, or Ordinal encoding

### AI Chat Examples
- "What are the main trends in this dataset?"
- "Which columns have the most missing values?"
- "Suggest preprocessing steps for this data"
- "What correlations exist between variables?"

## 🔧 Configuration

### Backend Configuration (.env)
```env
GOOGLE_API_KEY=your_api_key_here
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ENVIRONMENT=development
MAX_UPLOAD_SIZE=104857600
RATE_LIMIT_PER_MINUTE=60
```

### Frontend Configuration (frontend/.env)
```env
VITE_API_URL=http://localhost:8000
```

## 📁 Project Structure

```
minimal-eda-tarp/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration management
│   ├── db.py             # Database models
│   ├── helpers.py        # Utility functions
│   ├── schemas.py        # Pydantic models
│   └── logger.py         # Logging configuration
├── frontend/
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── styles/       # CSS modules
│   │   └── App.jsx       # Main app component
│   └── package.json
├── uploaded_files/       # File storage directory
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
```

## 🔐 Security Features

- Rate limiting (60 requests/minute)
- File type validation
- File size limits (100MB)
- SQL injection protection via SQLAlchemy
- CORS configuration
- Input validation with Pydantic

## 📊 API Endpoints

### Files
- `POST /api/upload` - Upload dataset
- `GET /api/datasets` - List all datasets
- `GET /api/dataset/{file_id}` - Get dataset info
- `DELETE /api/dataset/{file_id}` - Delete dataset
- `GET /api/download/{file_id}` - Download file

### Processing
- `POST /api/preprocess` - Preprocess dataset
- `POST /api/merge` - Merge multiple datasets

### Visualization
- `GET /api/visual_summary/{file_id}` - Generate automatic visualizations
- `POST /api/plot` - Create custom plot

### AI
- `POST /api/chat` - Chat with AI about dataset
- `GET /api/chat/history/{file_id}` - Get chat history

## 🚀 Production Deployment

### Using Docker (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Manual Deployment

#### Backend
```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Frontend
```bash
# Build for production
cd frontend
npm run build

# Serve with a static file server
npm install -g serve
serve -s dist -p 3000
```

## 🧪 Testing

```bash
# Backend tests
pytest backend/tests/

# Frontend tests
cd frontend
npm test
```

## 📝 Additional Features

### Data Quality Scoring
- Automatic calculation of data quality metrics
- Completeness, uniqueness, volume, and feature richness scores
- Visual indicators for data health

### Smart Preprocessing
- Intelligent suggestion of preprocessing steps
- Preserves data relationships
- Handles edge cases gracefully

### Interactive Visualizations
- Multiple chart types supported
- Automatic plot suggestions based on data types
- Export capabilities

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Troubleshooting

### Backend Issues
- **Port already in use**: Change `BACKEND_PORT` in .env
- **Database locked**: Delete `backend/eda_agent.db` and restart
- **Import errors**: Run `pip install -r requirements.txt`

### Frontend Issues
- **CORS errors**: Check `ALLOWED_ORIGINS` in backend .env
- **API connection failed**: Ensure backend is running on port 8000
- **Build errors**: Delete `node_modules` and run `npm install` again

### Node Version Warning
If you see Node.js version warnings, the app will still work with Node 20.17.0, though upgrading is recommended.

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Made with ❤️ - Production-Ready EDA Platform v2.0**
