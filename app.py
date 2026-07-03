"""
SpendWise AI — Enterprise Financial Audit & Budgeting Studio
A sleek, non-traditional Streamlit dashboard built for high-clarity expense analysis.
"""

import os
import json
import subprocess
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="SpendWise AI Studio",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def apply_custom_styles():
    """Injects professional CSS to transform standard Streamlit elements into a modern web app layout."""
    st.markdown(
        """
        <style>
        /* Import Google Typography */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        /* Global Font and App Background */
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
        }
        
        /* Hide default Streamlit header and footer for a native app feel */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Reduce top padding */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        /* Custom Top Navigation Bar */
        .top-navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 1.2rem 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
        }
        .nav-brand {
            font-size: 1.6rem;
            font-weight: 700;
            background: linear-gradient(90deg, #60A5FA, #A855F7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .nav-status {
            background: rgba(16, 185, 129, 0.15);
            color: #34D399;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            border: 1px solid rgba(52, 211, 153, 0.3);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* Modern KPI Cards */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.2rem;
            margin-bottom: 2rem;
        }
        .kpi-card {
            background: linear-gradient(145deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.8));
            border: 1px solid rgba(255, 255, 255, 0.07);
            padding: 1.5rem;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .kpi-card:hover {
            transform: translateY(-3px);
            border-color: rgba(96, 165, 250, 0.4);
        }
        .kpi-label {
            color: #94A3B8;
            font-size: 0.85rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }
        .kpi-value {
            color: #F8FAFC;
            font-size: 1.8rem;
            font-weight: 700;
        }
        .kpi-sub {
            color: #60A5FA;
            font-size: 0.8rem;
            margin-top: 0.4rem;
        }

        /* Feature & Coach Cards */
        .feature-card {
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.2rem;
        }
        .coach-card {
            background: linear-gradient(135deg, rgba(88, 28, 135, 0.25), rgba(30, 41, 59, 0.6));
            border-left: 4px solid #A855F7;
            padding: 1.2rem 1.5rem;
            border-radius: 12px;
            margin-bottom: 1rem;
        }
        .insight-badge {
            background: rgba(59, 130, 246, 0.15);
            color: #60A5FA;
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 0.5rem;
        }

        /* Streamlit Tabs Customization */
        stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: rgba(15, 23, 42, 0.6);
            padding: 8px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        stTabs [data-baseweb="tab"] {
            height: 45px;
            border-radius: 8px;
            font-weight: 600;
            color: #94A3B8;
        }
        stTabs [aria-selected="true"] {
            background-color: #3B82F6 !important;
            color: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

REPORT_PATH = "outputs/crew_analysis.json"
RECEIPTS_PATH = "outputs/categorized_receipts.json"

@st.cache_data
def load_spendwise_data():
    """Loads analyzed financial data from JSON outputs with easy fallback defaults."""
    report_data = {}
    receipts_data = []

    if os.path.exists(REPORT_PATH):
        try:
            with open(REPORT_PATH, "r", encoding="utf-8") as f:
                report_data = json.load(f)
        except Exception:
            pass

    if os.path.exists(RECEIPTS_PATH):
        try:
            with open(RECEIPTS_PATH, "r", encoding="utf-8") as f:
                receipts_data = json.load(f)
        except Exception:
            pass

    # Extract flat line items for DataFrame & table inspection
    items_list = []
    for doc in receipts_data:
        store = doc.get("merchant", "General Store")
        date = doc.get("date", "N/A")
        seq = doc.get("seq_no", 0)
        for item in doc.get("line_items", []):
            items_list.append({
                "Receipt ID": f"REC-{seq}",
                "Date": date,
                "Merchant": store,
                "Description": item.get("description", ""),
                "Category": item.get("category", "Uncategorized"),
                "Quantity": float(item.get("quantity", 1.0)),
                "Amount (₹)": float(item.get("amount", 0.0))
            })

    df_items = pd.DataFrame(items_list) if items_list else pd.DataFrame()
    return report_data, df_items

# ==========================================
# 3. UI COMPONENTS & RENDERING
# ==========================================
def render_navbar(total_items):
    """Renders a sleek top navigation header instead of standard Streamlit titles."""
    st.markdown(
        f"""
        <div class="top-navbar">
            <div class="nav-brand">
                <span>💎 SpendWise AI Studio</span>
            </div>
            <div class="nav-status">
                <span>●</span> Multi-Agent Audit Active ({total_items} Items Processed)
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_kpi_section(analysis, df_items):
    """Displays key performance indicators in custom HTML glassmorphic cards."""
    total_spent = float(analysis.get("total_spent", df_items["Amount (₹)"].sum() if not df_items.empty else 0.0))
    total_items = len(df_items)
    
    by_cat = analysis.get("by_category", {})
    top_cat = max(by_cat.items(), key=lambda x: x[1])[0] if by_cat else "N/A"
    top_cat_amt = by_cat.get(top_cat, 0.0) if by_cat else 0.0

    unique_merchants = df_items["Merchant"].nunique() if not df_items.empty else 0

    st.markdown(
        f"""
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total Verified Expenditure</div>
                <div class="kpi-value">₹{total_spent:,.2f}</div>
                <div class="kpi-sub">Audited by AI Accounting Engine</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Top Spending Area</div>
                <div class="kpi-value">{top_cat}</div>
                <div class="kpi-sub">₹{top_cat_amt:,.2f} of total budget</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Audited Line Items</div>
                <div class="kpi-value">{total_items}</div>
                <div class="kpi-sub">OCR Extracted & Classified</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Unique Merchants</div>
                <div class="kpi-value">{unique_merchants}</div>
                <div class="kpi-sub">Retail & Dining Vendors</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==========================================
# 4. MAIN APPLICATION FLOW
# ==========================================
def main():
    apply_custom_styles()
    report, df_items = load_spendwise_data()
    analysis = report.get("analysis", {})
    advice = report.get("advice", {})

    render_navbar(len(df_items))

    if df_items.empty and not analysis:
        st.warning("⚠️ No expenditure data found in `outputs/`. Please run the backend pipeline first (`python run.py`).")
        if st.button("🚀 Run Pipeline Now"):
            with st.spinner("Executing CrewAI Categorization & Audit..."):
                subprocess.run(["python", "run.py"])
                st.cache_data.clear()
                st.rerun()
        return

    # Render Executive KPI Section
    render_kpi_section(analysis, df_items)

    # Sleek Tabbed Workspace Layout
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚡ Executive Dashboard", 
        "🧠 AI Financial Coach", 
        "📑 Itemized Audit Ledger", 
        "⚙️ Pipeline Control"
    ])

    # ----------------------------------------------------
    # TAB 1: EXECUTIVE DASHBOARD
    # ----------------------------------------------------
    with tab1:
        col1, col2 = st.columns([1.3, 1])

        with col1:
            st.markdown("### 📊 Expenditure Distribution")
            by_category = analysis.get("by_category", {})
            if not by_category and not df_items.empty:
                by_category = df_items.groupby("Category")["Amount (₹)"].sum().to_dict()

            if by_category:
                df_cat = pd.DataFrame(list(by_category.items()), columns=["Category", "Amount"])
                fig_donut = px.pie(
                    df_cat, 
                    names="Category", 
                    values="Amount",
                    hole=0.55,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_donut.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E2E8F0"),
                    margin=dict(t=20, b=20, l=10, r=10),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                fig_donut.update_traces(hoverinfo="label+percent+value")
                st.plotly_chart(fig_donut, use_container_width=True)

        with col2:
            st.markdown("### 🔍 Senior Auditor Observations")
            insights = analysis.get("insights", [])
            if insights:
                for idx, insight in enumerate(insights, 1):
                    st.markdown(
                        f"""
                        <div class="feature-card">
                            <div class="insight-badge">Observation #{idx}</div>
                            <p style="margin: 0; color: #CBD5E1; font-size: 0.95rem; line-height: 1.5;">{insight}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("No auditor observations available yet.")

    # ----------------------------------------------------
    # TAB 2: AI FINANCIAL COACH
    # ----------------------------------------------------
    with tab2:
        st.markdown(f"### 🎓 Personalized Financial Advisory — Status: **{advice.get('budget_status', 'Healthy')}**")
        
        quick_win = advice.get("quick_win", "")
        if quick_win:
            st.markdown(
                f"""
                <div class="coach-card" style="border-left-color: #34D399; background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(30, 41, 59, 0.6));">
                    <h4 style="color: #34D399; margin-top: 0;">⚡ Immediate Quick Win</h4>
                    <p style="color: #F8FAFC; margin-bottom: 0;">{quick_win}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("#### Actionable Strategies & Tips")
        tips = advice.get("tips", [])
        for tip in tips:
            st.markdown(
                f"""
                <div class="feature-card" style="border-left: 4px solid #60A5FA;">
                    <p style="margin: 0; color: #E2E8F0;">💡 {tip}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        positive = advice.get("positive_note", "")
        if positive:
            st.success(f"🌟 **Encouragement:** {positive}")

    # ----------------------------------------------------
    # TAB 3: ITEMIZED AUDIT LEDGER
    # ----------------------------------------------------
    with tab3:
        st.markdown("### 📑 Verified Receipt Line Items")
        
        if not df_items.empty:
            # Interactive Filter Toolbar
            f_col1, f_col2, f_col3 = st.columns([1.5, 1, 1])
            with f_col1:
                search_query = st.text_input("🔎 Search description or merchant...", "")
            with f_col2:
                all_cats = ["All Categories"] + sorted(df_items["Category"].unique().tolist())
                selected_cat = st.selectbox("Filter Category", all_cats)
            with f_col3:
                all_merchants = ["All Merchants"] + sorted(df_items["Merchant"].unique().tolist())
                selected_merchant = st.selectbox("Filter Merchant", all_merchants)

            # Apply filters
            filtered_df = df_items.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df["Description"].str.contains(search_query, case=False, na=False) |
                    filtered_df["Merchant"].str.contains(search_query, case=False, na=False)
                ]
            if selected_cat != "All Categories":
                filtered_df = filtered_df[filtered_df["Category"] == selected_cat]
            if selected_merchant != "All Merchants":
                filtered_df = filtered_df[filtered_df["Merchant"] == selected_merchant]

            # Display clean styled table
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Amount (₹)": st.column_config.NumberColumn(format="₹%.2f")
                }
            )

            # Export Data Option
            csv_data = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Filtered Ledger (CSV)",
                data=csv_data,
                file_name="spendwise_audit_ledger.csv",
                mime="text/csv"
            )
        else:
            st.info("No itemized receipt ledger available.")

    # ----------------------------------------------------
    # TAB 4: PIPELINE CONTROL & DIAGNOSTICS
    # ----------------------------------------------------
    with tab4:
        st.markdown("### ⚙️ Multi-Agent Architecture & Execution")
        st.markdown(
            """
            SpendWise utilizes a 3-stage AI Crew architecture to audit receipts:
            1. **Item Categorizer Agent**: Examines OCR line items and maps them to clean financial buckets.
            2. **Senior Accounting Analyst**: Computes statistical patterns, frequency anomalies, and category concentration.
            3. **Student Financial Advisor**: Translates expenditure patterns into practical budgeting strategies.
            """
        )
        
        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 Re-Run Backend AI Pipeline (`run.py`)", use_container_width=True):
                with st.spinner("Orchestrating AI Crew pipeline... This may take several seconds."):
                    res = subprocess.run(["python", "run.py"], capture_output=True, text=True)
                    if res.returncode == 0:
                        st.success("✅ AI Analysis re-run successfully!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Error during execution:\n{res.stderr}")
        with col_b:
            if st.button("🧹 Clear App Cache", use_container_width=True):
                st.cache_data.clear()
                st.success("Cache cleared!")
                st.rerun()

if __name__ == "__main__":
    main()
