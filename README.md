# 🤖 DataColombus - Conversational EDA Agent
### *The Future of Data Analysis is Here - Chat Your Way to Insights*

<div align="center">

![Data Analysis](https://img.shields.io/badge/Data%20Analysis-AI%20Powered-blue?style=for-the-badge&logo=chart-dot-js)
![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)


<!-- 3D Rotating Data Visualization Animation -->
<img src="https://github.com/user-attachments/assets/data-visualization-3d.gif" width="600" alt="3D Data Visualization">

*Transform raw data into actionable insights through natural conversation*

</div>

---

## 🏗️ Architecture (Streamlit Version)

> See [ARCHITECTURE.md](ARCHITECTURE.md) for the full diagram and component breakdown.

```mermaid
graph TB
    User(["👤 User"])

    subgraph Streamlit["eda_agent_agentic.py — Streamlit App"]
        Sidebar["📁 Sidebar\nFile Upload & Management"]
        Tab1["🏠 Overview"]
        Tab2["🛠️ Tools\nPreprocessing · Merge · Plot"]
        Tab3["🤖 AI Chat"]
        Tab4["📊 Results"]
        Tab5["📈 Reports"]
        State["💾 Session State\nfiles · preprocessed_files\nchat_history · plot_cache"]

        subgraph Core["⚙️ Core Functions"]
            FileOps["File Ops\nload · add · get"]
            Analysis["Data Analysis\nprofile · smart-viz"]
            Preprocess["Preprocessing Pipeline\nmissing · outliers · scale\nencode · PCA · SMOTE"]
            VizEngine["Visualization Engine\n30+ chart types"]
            MergeOps["Merge Operations\nSQL joins · fuzzy match"]
        end

        subgraph Agent["🤖 LangGraph Agent"]
            AgentNode["Agent Node\nGemini 2.5 Flash"]
            ToolNode["Tool Node"]
        end
    end

    Gemini(["☁️ Google\nGemini API"])

    User -->|upload| Sidebar
    User -->|buttons| Tab2
    User -->|chat| Tab3
    Sidebar --> FileOps --> State
    Tab2 --> Preprocess & VizEngine & MergeOps --> State
    Tab3 --> AgentNode --> Gemini --> AgentNode
    AgentNode -- tool_calls --> ToolNode
    ToolNode --> Analysis & Preprocess & VizEngine & MergeOps
    ToolNode -- results --> AgentNode
    Tab4 -->|displays| State
    Tab5 -->|history| State
```

---


https://github.com/user-attachments/assets/376f9547-1458-4214-bd2c-17f02afd3545


### 🎪 **Live Demo Scenarios**

<table>
<tr>
<td width="33%">

**🔍 Natural Analysis**
```
💬 "What patterns do you see 
    in my sales data?"

✨ Gets instant insights:
   • Revenue trends
   • Customer segments  
   • Seasonal patterns
   • Anomaly detection
```

</td>
<td width="33%">

**🛠️ Smart Preprocessing**
```
💬 "Fill missing values with 
    mean and remove outliers"

✨ Auto-executes:
   • Missing data handling
   • Outlier detection
   • Data scaling  
   • Feature encoding
```

</td>
<td width="33%">

**📊 Instant Visualizations**
```
💬 "Create a 3D scatter plot 
    of age vs income vs score"

✨ Generates:
   • Interactive 3D plots
   • Correlation heatmaps
   • Distribution analysis
   • Custom dashboards
```

</td>
</tr>
</table>

---

## 🧠 **Core Capabilities**

### 🎯 **Autonomous AI Agent**

```mermaid
graph TD
    A[User Query] --> B{AI Agent}
    B --> C[Analyze Data]
    B --> D[Preprocess Dataset]
    B --> E[Create Visualizations]
    B --> F[Merge Files]
    
    C --> G[📊 Insights & Quality Score]
    D --> H[🧹 Clean, Scale, Encode]
    E --> I[📈 Interactive Plots]
    F --> J[🔗 Combined Dataset]
    
    G --> K[Natural Language Response]
    H --> K
    I --> K
    J --> K
```

### 🔧 **Advanced Preprocessing Pipeline**

<details>
<summary><strong>🛡️ Data Cleaning & Quality</strong></summary>

```python
✨ Missing Value Strategies:
   • Mean/Median/Mode imputation
   • KNN-based imputation  
   • Iterative imputation
   • Smart deletion

🎯 Outlier Detection:
   • IQR method
   • Z-score analysis
   • Isolation Forest
   • Statistical transformations

📊 Data Quality Scoring:
   • Completeness analysis
   • Consistency checks
   • Accuracy assessment
   • Reliability metrics
```

</details>

<details>
<summary><strong>⚙️ Feature Engineering</strong></summary>

```python
🔄 Scaling & Normalization:
   • MinMax scaling
   • Standard scaling
   • Robust scaling
   • Power transformations

🏷️ Encoding Strategies:
   • One-hot encoding
   • Ordinal encoding
   • Binary encoding
   • Target encoding

🎨 Advanced Features:
   • Polynomial features
   • Feature binning
   • Dimensionality reduction (PCA, t-SNE)
   • Feature selection
```

</details>

<details>
<summary><strong>🎭 ML-Ready Processing</strong></summary>

```python
⚖️ Imbalance Handling:
   • SMOTE oversampling
   • Random undersampling
   • Hybrid approaches

🔍 Feature Selection:
   • Variance thresholding
   • Statistical selection
   • Recursive elimination

🎯 Pipeline Ready:
   • Scikit-learn compatibility
   • Custom transformers
   • Automated workflows
```

</details>

### 📊 **Rich Visualization Suite**

<div align="center">

<!-- Visualization Types Animation -->
<img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=18&duration=2000&pause=500&color=F59E0B&center=true&vCenter=true&multiline=true&width=800&height=120&lines=📈+Correlation+Heatmaps+•+📊+3D+Scatter+Plots;🥧+Pie+Charts+•+📉+Distribution+Analysis;🗺️+Geographic+Maps+•+📋+Box+Plots;🌳+Treemaps+•+📊+Interactive+Dashboards" alt="Visualization Types">

</div>

## 📄 **License**

<div align="center">

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)


