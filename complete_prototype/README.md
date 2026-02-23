# Minimal EDA Tool - Complete Prototype

AI-powered exploratory data analysis tool with user authentication and dark theme UI.

## ✨ Features

- 🔐 **User Authentication** - Secure login/signup with bcrypt
- 📊 **Data Analysis** - Upload CSV, Excel, JSON files
- 🔧 **Preprocessing** - Handle missing values, outliers, scaling, encoding
- 📈 **Visualizations** - 8+ interactive chart types with Plotly
- 🤖 **AI Assistant** - Google Gemini-powered insights
- 📚 **History Tracking** - Save chats and uploaded files
- 🌙 **Dark Theme** - Eye-friendly purple/blue/pink gradient UI

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your Google Gemini API key:

```
GOOGLE_API_KEY=your_actual_api_key
DATABASE_URL=sqlite:///./users.db
```

Get a free API key at: https://makersuite.google.com/app/apikey

### 3. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 📁 Project Structure

```
complete_prototype/
├── app.py                  # Main Streamlit application
├── auth.py                 # Authentication & database
├── data_utils.py           # Data preprocessing utilities
├── ai_agent.py             # Google Gemini integration
├── visualizations.py       # Plotly chart functions
├── user_history.py         # History viewer
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── .streamlit/
│   └── config.toml        # Streamlit configuration
└── README.md              # This file
```

## 🌐 Deployment

### Deploy to Streamlit Cloud (Free)

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Add secrets in dashboard:
   ```
   GOOGLE_API_KEY = "your_key"
   DATABASE_URL = "your_cloud_database_url"
   ```
5. Deploy!

### Free Database Options

- **Supabase** (PostgreSQL): 500MB free
  ```
  DATABASE_URL=postgresql://user:pass@host/db
  ```

- **PlanetScale** (MySQL): 5GB free
  ```
  DATABASE_URL=mysql+pymysql://user:pass@host/db
  ```

- **SQLite** (local only):
  ```
  DATABASE_URL=sqlite:///./users.db
  ```

## 🎯 Usage

1. **Sign Up** - Create an account
2. **Upload Data** - Upload CSV/Excel/JSON file
3. **Explore** - View overview and statistics
4. **Preprocess** - Clean and transform data
5. **Visualize** - Create interactive charts
6. **Ask AI** - Get insights from Gemini
7. **Export** - Download processed data
8. **History** - View past chats and files

## 🔒 Security

- Passwords hashed with bcrypt
- Session tokens with 7-day expiry
- User data isolated per account
- Environment variables for sensitive data

## 📝 Technical Details

- **Frontend**: Streamlit with custom CSS
- **Database**: SQLAlchemy (SQLite/PostgreSQL/MySQL)
- **AI**: Google Gemini 2.0 Flash
- **Charts**: Plotly with dark theme
- **Data**: pandas, numpy, scikit-learn

## 🆘 Troubleshooting

**"No API key found"**
- Make sure `.env` file exists
- Check `GOOGLE_API_KEY` is set correctly

**"Database connection failed"**
- For cloud databases, verify connection string
- For local, ensure write permissions

**"Module not found"**
- Run `pip install -r requirements.txt`

## 📄 License

MIT License - See LICENSE file

## 👨‍💻 Author

Built with ❤️ for data analysis
