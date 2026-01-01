# 🤖 Autonomous Agent Features Guide

## Overview
The EDA Agent now features **truly autonomous AI** powered by Google Gemini that understands natural language requests from non-technical users and automatically executes the appropriate operations.

## How It Works

### 🧠 Intelligent Understanding
The agent uses Gemini's advanced language understanding to:
1. **Analyze the user's request** in plain, natural language
2. **Inspect the dataset** characteristics (missing values, data types, cardinality)
3. **Make smart decisions** about what operations to perform
4. **Execute automatically** without requiring specific keywords

### 🎯 Intent Recognition

The agent recognizes four main intents:

#### 1. **ANALYZE** - Data Exploration
User wants to understand the dataset structure and statistics.

**Example Prompts:**
- "Analyze this dataset"
- "What's in this data?"
- "Show me dataset summary"
- "Tell me about this file"

**What It Does:**
- Shows shape, columns, data types
- Displays missing value statistics
- Highlights high-missing columns (>70%)
- Provides statistical summary

#### 2. **VISUALIZE** - Automatic Plot Generation
User wants charts and visualizations.

**Example Prompts:**
- "Visualize this dataset"
- "Create plots for me"
- "Show me charts"
- "Plot everything possible"

**What It Does:**
- Generates 8+ smart visualizations automatically
- Saves all plots to database
- Makes them downloadable as PNG/ZIP
- Includes: distributions, correlations, relationships, categorical analysis

#### 3. **PREPROCESS** - Intelligent Data Cleaning
User wants data preprocessing and transformation.

**Example Prompts (Generic - No Keywords Needed!):**
- "Clean my data"
- "Preprocess this dataset"
- "Prepare data for machine learning"
- "Fix missing values appropriately"
- "Clean and encode everything"

**What It Does:**
The agent **inspects your data** and automatically decides:

**Missing Values:**
- High outlier-sensitive data → Uses **median**
- Normal distribution → Uses **mean**
- Complex patterns → Uses **KNN imputation**
- >70% missing → Recommends **dropping** the column

**Outlier Handling:**
- Detects outliers using IQR/Z-score/Isolation Forest
- Caps extreme values automatically
- Preserves data distribution

**Categorical Encoding:**
- Low cardinality (<10 unique) → **One-hot encoding**
- High cardinality (>50 unique) → **Label encoding** or **drop**
- Ordinal data → **Ordinal encoding**

**Scaling:**
- Outliers present → **Robust scaling**
- Normal distribution → **Standard scaling**
- Bounded range needed → **MinMax scaling**

**Column Dropping:**
- Automatically drops columns like:
  - High missing (>70%): Cabin, PassengerId, etc.
  - Irrelevant IDs: Ticket, Name, etc.
  - Redundant features

**Saves to Database:**
- Creates new preprocessed file
- Generates unique file_id
- Makes it downloadable immediately
- Shows before/after comparison

#### 4. **EXPLAIN** - Conversational Help
User asks questions or needs explanations.

**Example Prompts:**
- "How should I clean this?"
- "What preprocessing is recommended?"
- "Explain the columns"
- "What analysis can I do?"

**What It Does:**
- Provides helpful explanations
- Suggests next steps
- No automatic execution (safe mode)

## 🎨 User Interface Features

### Example Prompts (Quick Start)
When you first open the chat, you'll see clickable example prompts:
- "Analyze this dataset"
- "Visualize all possible insights"
- "Clean and preprocess my data"
- "Fill missing values appropriately"
- "Show me plots for this data"
- "What's in this dataset?"

Just **click any example** to try it instantly!

### Download Options
Every operation that creates results includes download buttons:
- **Preprocessed Data**: Download CSV from Preprocess Panel
- **Visualizations**: Download individual PNGs or ZIP of all plots
- **Chat Interface**: "Download Plots" button for all AI-generated visualizations

## 🚀 Advanced Usage

### Natural Language Processing
The agent understands **context and intent**, not just keywords:

❌ **Old Way (Keyword-Based):**
- "use median for missing values and onehot encoding and standard scaling"
- Required specific terms like "median", "onehot", "standard"

✅ **New Way (Autonomous):**
- "clean my data appropriately"
- "preprocess for machine learning"
- "fix everything automatically"

The agent figures out the rest!

### Smart Decision Making
The agent inspects your data to make intelligent choices:

**Example: Titanic Dataset**
```
Columns: PassengerId, Name, Age, Cabin, Survived, Pclass, Sex, Embarked
```

**What The Agent Automatically Does:**
1. **Drops** PassengerId, Name (irrelevant IDs)
2. **Drops** Cabin (>70% missing)
3. **Fills** Age with **median** (has outliers)
4. **Encodes** Sex, Embarked with **one-hot** (low cardinality)
5. **Scales** numeric features with **standard scaling**
6. **Saves** cleaned dataset with new file_id

All from just saying: **"preprocess this dataset"**!

## 📊 Supported Operations

### Preprocessing Techniques (Auto-Configured)
- ✅ Missing value imputation (mean/median/KNN/iterative)
- ✅ Outlier detection and handling (IQR/Z-score/Isolation Forest)
- ✅ Categorical encoding (one-hot/label/ordinal/binary/frequency/target)
- ✅ Numeric scaling (standard/minmax/robust/power transform)
- ✅ Dimensionality reduction (PCA/t-SNE/LDA/TruncatedSVD)
- ✅ Feature selection (variance threshold/SelectKBest/chi2)
- ✅ Class imbalancing handling (SMOTE/RandomUnderSampler)
- ✅ Feature engineering (polynomial features/binning/log transform)
- ✅ Column dropping (high missing/low variance/irrelevant)

### Visualization Types (Auto-Generated)
- 📊 Distribution plots (histogram, KDE, violin, box)
- 📈 Correlation heatmaps and pair plots
- 🎯 Scatter plots (2D, 3D) with color/size encoding
- 📉 Line plots and time series
- 🥧 Pie charts and sunbursts
- 📦 Box plots and violin plots
- 🔥 Heatmaps and cluster maps
- 🌐 3D surface and mesh plots
- And 20+ more plot types!

## 🎓 Tips for Non-Technical Users

### Use Simple, Natural Language
- ✅ "clean this data"
- ✅ "make some plots"
- ✅ "what's wrong with my dataset?"
- ✅ "prepare for analysis"

### No Need for Technical Terms
You **don't need to know**:
- What "median imputation" means
- Difference between "one-hot" and "label encoding"
- When to use "robust" vs "standard" scaling
- How to detect outliers

**The agent figures it all out!**

### Ask Follow-Up Questions
- "Why did you drop these columns?"
- "What does this plot show?"
- "Should I do more preprocessing?"
- "What analysis can I do next?"

### Trust the Agent
The autonomous system is designed to:
- ✅ Make statistically sound decisions
- ✅ Follow data science best practices
- ✅ Preserve data integrity
- ✅ Explain what it did

## 🔧 Technical Details (For Developers)

### Architecture
1. **Gemini Intent Parser**: Analyzes request + data characteristics → structured JSON plan
2. **Smart Execution Engine**: Executes the plan with optimal parameters
3. **Database Integration**: Saves results (plots, preprocessed files) to SQLite
4. **Fallback System**: Keyword-based detection if autonomous mode fails

### Code Location
- **Backend**: `backend/helpers.py`
  - `ai_analysis_gemini_agentic()` - Main autonomous agent
  - `ai_analysis_gemini_agentic_fallback()` - Keyword-based fallback
  - `preprocess_dataset()` - Preprocessing engine (30+ parameters)
  - `create_smart_visualizations()` - Auto plot generation

### Comparison with Streamlit Version
| Feature | Streamlit (Original) | React (Current) |
|---------|---------------------|-----------------|
| Natural Language | ✅ LangGraph | ✅ Gemini Function Calling |
| Intent Recognition | ✅ Tool Selection | ✅ JSON-based Planning |
| Auto-Preprocessing | ✅ @tool decorator | ✅ Smart Config Builder |
| Plot Generation | ✅ Saved to cache | ✅ Saved to database |
| Download Options | ✅ Streamlit UI | ✅ React components |
| Non-Technical Friendly | ✅ Yes | ✅ Yes |

Both achieve the same **autonomous behavior** with different implementations!

## 🐛 Troubleshooting

### "AI analysis temporarily unavailable"
- Check GOOGLE_API_KEY in `.env`
- Verify API quota on Google Cloud Console
- System automatically falls back to keyword detection

### "Preprocessing failed"
- Dataset might be too small (<10 rows)
- All columns might be non-numeric
- Try being more specific: "fill missing with mean and encode sex column"

### Plots not generated
- Check dataset has numeric/categorical columns
- Try: "create scatter plot of age vs fare"
- Verify plots in Visualization Panel

## 📚 Examples from Real Usage

### Example 1: Titanic Dataset
**User:** "preprocess this dataset appropriately"

**Agent Response:**
```
✅ Preprocessing Complete!

Operations Performed:
• Dropped columns: PassengerId, Name, Cabin (high missing/irrelevant)
• Filled Age with median (82 missing values)
• Filled Embarked with mode (2 missing values)
• Encoded Sex with one-hot encoding
• Encoded Embarked with one-hot encoding
• Scaled numeric features with standard scaling
• Handled outliers using IQR method (capped)

Before: 891 rows × 12 columns
After: 891 rows × 15 columns

New File ID: 7ad3f90f-b22b-49fc-ab72-0c4b9db118db

📥 Download the preprocessed dataset from the Preprocess Panel!
```

### Example 2: Insurance Dataset
**User:** "show me visualizations"

**Agent Response:**
```
✅ Generated 8 visualizations!

Plots created:
• Age Distribution (Histogram)
• BMI vs Charges (Scatter with Smoker color)
• Correlation Heatmap
• Charges by Region (Box Plot)
• Age vs BMI vs Charges (3D Scatter)
• Smoker Distribution (Pie Chart)
• Children Count (Bar Chart)
• BMI Distribution (Violin Plot)

📥 Download them from the Visualization Panel or use the 'Download Plots' button!
```

### Example 3: Generic Question
**User:** "what should i do with this data?"

**Agent Response:**
```
Based on your dataset (891 rows × 12 columns):

Recommended Steps:
1. Preprocess: Handle missing values in Age (82 missing), Cabin (687 missing)
2. Visualize: Create plots to understand Survived vs features
3. Analyze: Look at correlations between Age, Fare, Pclass and Survived
4. Encode: Convert Sex and Embarked to numeric
5. Drop: Consider dropping Cabin (77% missing) and Name/Ticket (IDs)

Try saying:
- "clean my data" → Automatic preprocessing
- "visualize everything" → Auto-generate plots
- "analyze survival patterns" → Statistical insights
```

## 🎉 Success!

You now have a **truly autonomous EDA agent** that:
- ✅ Understands natural language from non-technical users
- ✅ Makes intelligent decisions based on data inspection
- ✅ Automatically executes preprocessing with smart defaults
- ✅ Generates visualizations and saves them to database
- ✅ Provides downloadable results for all operations
- ✅ Matches Streamlit's autonomous behavior in React!

**Just upload your data and start chatting naturally!** 🚀
