# 🏗️ Architecture Diagram — Streamlit Version

> This document describes the architecture of the **Streamlit-based** Conversational EDA Agent (`eda_agent_agentic.py`).

---

## Overview

```mermaid
graph TB
    User(["👤 User"])

    subgraph StreamlitApp["eda_agent_agentic.py  —  Streamlit Application"]

        subgraph UILayer["🖥️  UI Layer"]
            Sidebar["📁 Sidebar\n─────────────\nFile Upload\n(CSV / Excel)\n\nLoaded Files List\n& Remove Controls"]
            Tab1["🏠 Tab 1 · Overview\n─────────────\nDataset Metrics\nData Preview\nQuick Analysis\nAuto Visualize"]
            Tab2["🛠️ Tab 2 · Tools\n─────────────\nSmart Clean\nFull Preprocess\nCustom Preprocessing\nData Merger\nPlot Generator"]
            Tab3["🤖 Tab 3 · AI Chat\n─────────────\nConversational\nAgent Interface\nChat History"]
            Tab4["📊 Tab 4 · Results\n─────────────\nInteractive Plots\nPreprocessed Files\nDownload Buttons"]
            Tab5["📈 Tab 5 · Reports\n─────────────\nProcessing\nHistory Log"]
        end

        subgraph StateLayer["💾  Session State  (st.session_state)"]
            S_Files["files\n{idx → df + FileMetadata}"]
            S_Pre["preprocessed_files\n{name → DataFrame}"]
            S_Hist["processing_history\n[ProcessingHistory]"]
            S_Chat["chat_history\n[{role, content}]"]
            S_Plots["plot_cache\n{key → [(title, fig)]}"]
        end

        subgraph CoreLayer["⚙️  Core Functions"]

            subgraph FileOps["File Operations"]
                FO1["load_file_buffer()\nCSV / Excel → DataFrame\nmulti-encoding support"]
                FO2["add_file()\nDataFrame + FileMetadata\n→ session_state.files"]
                FO3["get_file_by_ref()\nresolve by index / name"]
            end

            subgraph AnalysisOps["Data Analysis"]
                AN1["generate_data_profile()\nshape · dtypes · missing\nduplicates · quality score\nstatistics · correlations"]
                AN2["create_smart_visualizations()\nauto-selects best plot types\nreturns up to N plotly figs"]
            end

            subgraph PrepOps["Preprocessing Pipeline\n(enhanced_preprocessing)"]
                PP1["Missing Values\nmean · median · mode\nKNN · Iterative · drop"]
                PP2["Outlier Handling\nIQR · Z-score\nIsolation Forest\ncap · remove · transform"]
                PP3["Scaling\nMinMax · Standard\nRobust · Power"]
                PP4["Encoding\nOneHot · Label · Ordinal\nBinary · Frequency · Target"]
                PP5["Dimensionality Reduction\nPCA · t-SNE · SVD · LDA"]
                PP6["Feature Selection\nVariance · K-Best\nRandom Forest Importance"]
                PP7["Imbalance Handling\nSMOTE · Undersampling"]
                PP8["Feature Engineering\nPolynomial · Binning"]
            end

            subgraph VizOps["Visualization Engine"]
                V1["create_custom_plot()\nscatter · line · bar · pie\nheatmap · 3D · sunburst\ntreemap · choropleth · …"]
                V2["generate_auto_plot()\nfallback auto-plot"]
            end

            subgraph MergeOps["Merge Operations\n(merge_dataframes)"]
                M1["SQL-style joins\ninner · outer · left · right · cross"]
                M2["Fuzzy Matching\n(fuzzywuzzy · recordlinkage)"]
                M3["Concatenation\naxis 0 / 1"]
            end

        end

        subgraph AgentLayer["🤖  LangGraph Agent"]
            direction LR
            AG["Agent Node\n─────────────\nChatGoogleGenerativeAI\ngemini-2.5-flash\n\nSystem prompt with\nfile context & tool docs"]
            TN["Tool Node\n─────────────\nDispatches tool_calls\nfrom last AIMessage"]
            T_A["analyze_data_tool\n→ generate_data_profile"]
            T_P["preprocess_data_tool\n→ enhanced_preprocessing"]
            T_V["create_visualization_tool\n→ create_custom_plot"]
            T_M["merge_files_tool\n→ merge_dataframes"]

            AG -- "has tool_calls" --> TN
            TN --> T_A
            TN --> T_P
            TN --> T_V
            TN --> T_M
            TN -- "ToolMessages" --> AG
            AG -- "no tool_calls" --> END_NODE(["END"])
        end

    end

    subgraph ExternalLayer["☁️  External Services"]
        GEM["Google Gemini API\ngemini-2.5-flash\n(LLM + Tool Calling)"]
    end

    %% User interactions
    User -->|"upload file"| Sidebar
    User -->|"click buttons"| Tab2
    User -->|"type message"| Tab3

    %% Sidebar → file ops → state
    Sidebar -->|"uploaded_file"| FO1
    FO1 --> FO2
    FO2 -->|"stores"| S_Files

    %% Tab1 reads state
    Tab1 -->|"reads"| S_Files
    Tab1 -->|"calls"| AN1
    Tab1 -->|"calls"| AN2

    %% Tab2 calls core
    Tab2 -->|"calls"| PrepOps
    Tab2 -->|"calls"| VizOps
    Tab2 -->|"calls"| MergeOps
    PrepOps -->|"stores"| S_Pre
    PrepOps -->|"appends"| S_Hist
    VizOps -->|"stores"| S_Plots

    %% Tab3 → agent
    Tab3 -->|"HumanMessage"| AG
    Tab3 -->|"reads / writes"| S_Chat
    AG -->|"API call"| GEM
    GEM -->|"AIMessage"| AG

    %% Agent tools read/write state
    T_A -->|"reads"| S_Files
    T_P -->|"reads"| S_Files
    T_P -->|"stores"| S_Pre
    T_V -->|"reads"| S_Files
    T_V -->|"stores"| S_Plots
    T_M -->|"reads"| S_Files
    T_M -->|"stores"| S_Pre

    %% Tab4 displays results
    Tab4 -->|"displays"| S_Plots
    Tab4 -->|"downloads"| S_Pre

    %% Tab5 reads history
    Tab5 -->|"displays"| S_Hist
```

---

## Component Breakdown

| Layer | Component | Description |
|-------|-----------|-------------|
| **UI** | Sidebar | CSV/Excel file upload; lists loaded files with remove controls |
| **UI** | Tab 1 — Overview | Summary metrics (rows/cols/size), per-file data preview, quick analysis and auto-visualize buttons |
| **UI** | Tab 2 — Tools | One-click Quick Actions; advanced Custom Preprocessing form; Data Merger; Plot Generator |
| **UI** | Tab 3 — AI Chat | Full conversational interface backed by the LangGraph agent |
| **UI** | Tab 4 — Results | Renders cached interactive plots; lists downloadable preprocessed files |
| **UI** | Tab 5 — Reports | Shows the ordered processing history log |
| **State** | `files` | Dict mapping int ID → `{df: DataFrame, metadata: FileMetadata}` |
| **State** | `preprocessed_files` | Dict mapping filename → processed DataFrame |
| **State** | `processing_history` | List of `ProcessingHistory` dataclasses (action, params, timestamp, shape, status) |
| **State** | `chat_history` | List of `{role, content}` dicts for chat display |
| **State** | `plot_cache` | Dict mapping cache key → list of `(title, figure)` tuples |
| **Core** | File Operations | `load_file_buffer` (multi-encoding CSV/XLSX), `add_file`, `get_file_by_ref` |
| **Core** | Data Analysis | `generate_data_profile` (quality score, stats, correlations), `create_smart_visualizations` |
| **Core** | Preprocessing | `enhanced_preprocessing` — 8-stage pipeline (see below) |
| **Core** | Visualization | `create_custom_plot` (30+ chart types via Plotly/Seaborn), `generate_auto_plot` |
| **Core** | Merge | `merge_dataframes` — SQL joins, concat, and fuzzy matching via fuzzywuzzy/recordlinkage |
| **Agent** | Agent Node | `ChatGoogleGenerativeAI` (Gemini 2.5 Flash) with system prompt carrying file context |
| **Agent** | Tool Node | Executes `tool_calls` from the last `AIMessage`, returns `ToolMessage` results |
| **Agent** | Tools | `analyze_data_tool`, `preprocess_data_tool`, `create_visualization_tool`, `merge_files_tool` |
| **External** | Google Gemini API | LLM backend for reasoning and tool-call generation |

---

## Preprocessing Pipeline Stages

```
enhanced_preprocessing(df, params)
  │
  ├─ 1. Missing Values      → mean / median / mode / KNN / Iterative / drop
  ├─ 2. Outlier Handling    → IQR / Z-score / Isolation Forest  →  cap / remove / transform
  ├─ 3. Scaling             → MinMax / Standard / Robust / Power (Yeo-Johnson / Box-Cox)
  ├─ 4. Encoding            → OneHot / Label / Ordinal / Binary / Frequency / Target
  ├─ 5. Dim. Reduction      → PCA / t-SNE / TruncatedSVD / LDA
  ├─ 6. Feature Selection   → Variance threshold / SelectKBest / Random Forest importance
  ├─ 7. Imbalance Handling  → SMOTE (oversampling) / Random Undersampling
  └─ 8. Feature Engineering → Polynomial features / Column binning
```

---

## LangGraph Agent Flow

```
User message
    │
    ▼
[Agent Node] ── system prompt + available tools ──► Google Gemini API
    │                                                       │
    │◄──────────────── AIMessage (± tool_calls) ────────────┘
    │
    ├── No tool_calls ──► END  (reply shown to user)
    │
    └── Has tool_calls
            │
            ▼
       [Tool Node]
            │
            ├── analyze_data_tool     → generate_data_profile
            ├── preprocess_data_tool  → enhanced_preprocessing
            ├── create_visualization_tool → create_custom_plot
            └── merge_files_tool      → merge_dataframes
            │
            ▼
       ToolMessage results
            │
            ▼
       [Agent Node]  ← loop back for summary reply
```

---

## Key Libraries

| Purpose | Library |
|---------|---------|
| Web UI | `streamlit` |
| Data wrangling | `pandas`, `numpy` |
| Preprocessing & ML | `scikit-learn`, `imbalanced-learn` |
| Statistics | `scipy` |
| Visualization | `plotly`, `matplotlib`, `seaborn` |
| Fuzzy matching | `fuzzywuzzy`, `recordlinkage` |
| LLM / Agent | `langchain-google-genai`, `langgraph`, `langchain-core` |
| LLM backend | Google Gemini API (`google-generativeai`) |
