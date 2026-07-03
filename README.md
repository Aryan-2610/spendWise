# 💎 SpendWise AI Studio

An enterprise-grade, multi-agent financial audit and smart budgeting platform powered by **CrewAI**, **HuggingFace OCR**, and a **Modern Streamlit Studio**.

SpendWise automatically extracts retail line items from receipt images, uses autonomous AI agents to classify expenses, computes statistical anomalies, and delivers personalized student financial coaching in a stunning, non-traditional web interface.

---

## ✨ Features & Architecture

### 🤖 Multi-Agent AI Engine (`run.py`)
SpendWise orchestrates a sequential 3-agent AI Crew:
1. **Item Categorizer Agent**: Examines raw OCR line items and intelligently assigns them to standardized financial categories (*Groceries, Snacks, Entertainment, Medical, etc.*).
2. **Senior Accounting Analyst**: Audits item frequency, price anomalies, and concentration of expenditure across categories.
3. **Student Financial Coach**: Translates expenditure observations into highly actionable budgeting strategies and immediate "quick wins."

### 🎨 Non-Traditional Studio Layout (`app.py`)
Unlike standard Streamlit scripts that rely on basic titles and cluttered sidebars, SpendWise AI Studio features a **custom web-app aesthetic**:
- **Glassmorphic Top Navbar**: A sleek status bar displaying real-time audit health and live item counts.
- **HTML/CSS KPI Cards**: Interactive summary cards with subtle hover effects, gradients, and custom badges.
- **Segmented Workspace Tabs**: Clean separation of concerns into *Executive Dashboard*, *AI Financial Coach*, *Itemized Audit Ledger*, and *Pipeline Control*.
- **Interactive Visualizations**: Donut charts powered by **Plotly Express** with custom dark-themed styling.
- **Interactive Ledger**: Search, filter by merchant or category, and one-click export to CSV.

---

## 🚀 Quickstart Guide

### 1. Environment Setup
Make sure you have Python 3.10+ installed and activate your virtual environment:

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (if not already installed)
pip install streamlit plotly pandas crewai
```

### 2. Step 1: Scan Receipts (OCR Extraction)
Extract itemized data from receipt images:
```bash
python scan-reciepts-hf.py
```
*(Outputs raw receipt items to `outputs/ocr_results.json`)*

### 3. Step 2: Run Multi-Agent AI Audit
Execute the CrewAI accounting & advisory pipeline:
```bash
python run.py
```
*(Outputs classified receipts to `outputs/categorized_receipts.json` and the audit report to `outputs/crew_analysis.json`)*

### 4. Step 3: Launch SpendWise Studio Dashboard
Launch the interactive web application:
```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501` to view your live financial dashboard!

---

## 📂 Project Structure

```text
spendWise/
├── app.py                     # Modern Streamlit Studio Dashboard (Non-standard layout)
├── run.py                     # CrewAI multi-agent orchestration pipeline
├── agents_And_tasks.py        # Definition of Categorizer, Analyst, and Advisor agents
├── scan-reciepts-hf.py        # Receipt OCR ingestion engine
├── analysis.py                # CLI terminal dashboard utility
├── outputs/                   # JSON storage for OCR and audited reports
│   ├── ocr_results.json
│   ├── categorized_receipts.json
│   └── crew_analysis.json
├── receipts/                  # Input receipt images
└── README.md                  # Project documentation
```

---

## 💡 Code Design Philosophy (`app.py`)
The Streamlit application is designed to be **clean, modular, and easy to modify**:
- **Separation of Concerns**: UI rendering is broken down into clean helper functions (`render_navbar`, `render_kpi_section`).
- **Fast Caching**: `@st.cache_data` ensures instantaneous loads when switching tabs or filtering data.
- **In-App Control**: Users can re-trigger the backend AI Crew directly from the *Pipeline Control* tab without touching the command line.
