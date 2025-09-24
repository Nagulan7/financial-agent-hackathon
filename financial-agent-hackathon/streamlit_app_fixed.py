import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from main_refactored import load_and_analyze_for_streamlit
from utils.data_loader import load_transactions
import os
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Financial Agent - Transaction Analyzer",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.user-card {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 10px;
    border-left: 4px solid #1f77b4;
    margin-bottom: 1rem;
}
.metric-card {
    background-color: #fff;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}
.category-spending {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None

def load_and_analyze_data(file_path=None, uploaded_file=None):
    """Load and analyze transaction data using the refactored functions"""
    try:
        if uploaded_file is not None:
            # Handle uploaded file
            df = pd.read_excel(uploaded_file)
            return load_and_analyze_for_streamlit(df=df)
        else:
            # Use default file
            return load_and_analyze_for_streamlit(file_path)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

def create_spending_chart(user_data):
    """Create spending breakdown chart"""
    analysis = user_data.get('pandas_analysis', {})
    
    if not analysis:
        return None
    
    # Extract category spending from analysis
    category_data = []
    if 'category_spending' in analysis:
        for category, amount in analysis['category_spending'].items():
            category_data.append({'Category': category, 'Amount': amount})
    
    if not category_data:
        # Fallback: create category data from transactions
        transactions_df = user_data.get('transactions_df', pd.DataFrame())
        if not transactions_df.empty and 'category' in transactions_df.columns:
            category_spending = transactions_df.groupby('category')['amount'].sum()
            for category, amount in category_spending.items():
                category_data.append({'Category': category, 'Amount': amount})
    
    if not category_data:
        return None
        
    df_categories = pd.DataFrame(category_data)
    
    # Create pie chart
    fig = px.pie(df_categories, values='Amount', names='Category', 
                 title="💰 Spending by Category",
                 color_discrete_sequence=px.colors.qualitative.Set3)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=True)
    return fig

def create_transaction_timeline(transactions_df):
    """Create transaction timeline chart"""
    if transactions_df.empty:
        return None
        
    # Convert date column to datetime - check for actual column names
    date_col = None
    for col in ['timestamp', 'date', 'Date', 'transaction_date', 'Date_Time']:
        if col in transactions_df.columns:
            date_col = col
            break
    
    if date_col:
        df_copy = transactions_df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy = df_copy.dropna(subset=[date_col])
        
        if not df_copy.empty:
            daily_spending = df_copy.groupby(df_copy[date_col].dt.date)['amount'].sum().reset_index()
            daily_spending.columns = ['Date', 'Amount']
            
            fig = px.line(daily_spending, x='Date', y='Amount',
                         title="📈 Daily Spending Trend",
                         markers=True)
            fig.update_layout(
                xaxis_title="Date", 
                yaxis_title="Amount (₹)",
                hovermode='x unified'
            )
            fig.update_traces(line_color='#1f77b4', marker_size=6)
            return fig
    
    return None

def create_merchant_chart(transactions_df):
    """Create top merchants chart"""
    # Check for the correct merchant column name
    merchant_col = None
    for col in ['merchant_name', 'merchant', 'Merchant']:
        if col in transactions_df.columns:
            merchant_col = col
            break
    
    if transactions_df.empty or merchant_col is None:
        return None
        
    merchant_spending = transactions_df.groupby(merchant_col)['amount'].sum().sort_values(ascending=False).head(10)
    
    if merchant_spending.empty:
        return None
    
    fig = px.bar(
        x=merchant_spending.values, 
        y=merchant_spending.index, 
        orientation='h', 
        title="🏪 Top 10 Merchants by Spending",
        color=merchant_spending.values,
        color_continuous_scale='Blues'
    )
    fig.update_layout(
        xaxis_title="Amount (₹)", 
        yaxis_title="Merchant",
        coloraxis_showscale=False
    )
    return fig

def display_user_analysis(user_id, user_data):
    """Display comprehensive analysis for a user"""
    st.markdown(f"""
    <div class="user-card">
        <h2>👤 Financial Profile: {user_id}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    analysis = user_data.get('pandas_analysis', {})
    transactions_df = user_data.get('transactions_df', pd.DataFrame())
    
    if analysis:
        with col1:
            total_spending = analysis.get('total_spending', 0)
            st.metric("Total Spending", f"₹{total_spending:,.2f}")
        
        with col2:
            total_transactions = analysis.get('total_transactions', 0)
            st.metric("Total Transactions", f"{total_transactions:,}")
        
        with col3:
            avg_transaction = analysis.get('average_transaction_amount', 0)
            st.metric("Avg Transaction", f"₹{avg_transaction:.2f}")
        
        with col4:
            unique_merchants = analysis.get('unique_merchants', 0)
            st.metric("Unique Merchants", f"{unique_merchants}")
    
    # Charts section
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        spending_chart = create_spending_chart(user_data)
        if spending_chart:
            st.plotly_chart(spending_chart, use_container_width=True)
    
    with chart_col2:
        merchant_chart = create_merchant_chart(transactions_df)
        if merchant_chart:
            st.plotly_chart(merchant_chart, use_container_width=True)
    
    # Timeline chart
    timeline_chart = create_transaction_timeline(transactions_df)
    if timeline_chart:
        st.plotly_chart(timeline_chart, use_container_width=True)
    
    # AI-Generated Profile
    st.subheader("🤖 AI-Generated Financial Insights")
    profile = user_data.get('profile_summary', 'No profile available')
    # Process the profile text to handle markdown-like formatting
    profile_formatted = profile.replace('**', '**').replace('\n', '<br>')
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
        {profile_formatted}
    </div>
    """, unsafe_allow_html=True)
    
    # Transaction details
    if not transactions_df.empty:
        st.subheader("📋 Recent Transactions")
        # Use the correct column names from the dataset
        col_mapping = {
            'merchant_name': 'Merchant',
            'category': 'Category', 
            'amount': 'Amount',
            'timestamp': 'Date',
            'transaction_type': 'Type',
            'status': 'Status'
        }
        
        # Only include columns that exist in the DataFrame
        available_cols = []
        for col, display_name in col_mapping.items():
            if col in transactions_df.columns:
                available_cols.append(col)
        
        if available_cols:
            display_df = transactions_df.head(10)[available_cols].copy()
            # Rename columns for better display
            rename_dict = {col: col_mapping[col] for col in available_cols if col in col_mapping}
            display_df = display_df.rename(columns=rename_dict)
            
            # Sort by timestamp if available
            if 'Date' in display_df.columns:
                display_df = display_df.sort_values('Date', ascending=False)
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.dataframe(transactions_df.head(10), use_container_width=True)

def main():
    """Main Streamlit app"""
    # Header
    st.markdown('<p class="main-header">💰 Financial Agent - Transaction Analyzer</p>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("📊 Analysis Options")
    
    # File upload option
    uploaded_file = st.sidebar.file_uploader(
        "Upload Transaction File", 
        type=['xlsx', 'csv'],
        help="Upload your transaction data file (Excel or CSV format)"
    )
    
    use_sample_data = st.sidebar.checkbox(
        "Use Sample Data", 
        value=True,
        help="Use the provided sample UPI transactions data"
    )
    
    # Analysis button
    if st.sidebar.button("🔍 Analyze Transactions", type="primary"):
        with st.spinner("Loading and analyzing transaction data..."):
            if use_sample_data and not uploaded_file:
                data, results = load_and_analyze_data("sample_data/upi_transactions.xlsx")
            elif uploaded_file:
                data, results = load_and_analyze_data(uploaded_file=uploaded_file)
            else:
                st.error("Please upload a file or use sample data")
                return
            
            if results:
                st.session_state.analysis_results = results
                st.session_state.processed_data = data
                st.success(f"✅ Analysis complete! Found {len(results)} users with {len(data)} total transactions.")
    
    # Display results
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        
        # Overview metrics
        st.subheader("📈 Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        total_users = len(results)
        total_transactions = len(st.session_state.processed_data) if st.session_state.processed_data is not None else 0
        total_spending = sum([r.get('pandas_analysis', {}).get('total_spending', 0) for r in results.values()])
        avg_spending = total_spending / total_users if total_users > 0 else 0
        
        with col1:
            st.metric("Total Users", f"{total_users}")
        with col2:
            st.metric("Total Transactions", f"{total_transactions:,}")
        with col3:
            st.metric("Total Spending", f"₹{total_spending:,.2f}")
        with col4:
            st.metric("Avg Spending/User", f"₹{avg_spending:,.2f}")
        
        # User selection
        st.subheader("👥 User Analysis")
        selected_user = st.selectbox(
            "Select a user to view detailed analysis:",
            options=list(results.keys()),
            help="Choose a user ID to see their detailed financial analysis"
        )
        
        if selected_user:
            display_user_analysis(selected_user, results[selected_user])
        
        # Comparison section
        if len(results) > 1:
            st.subheader("📊 User Comparison")
            
            # Create comparison data
            comparison_data = []
            for user_id, data in results.items():
                analysis = data.get('pandas_analysis', {})
                comparison_data.append({
                    'User': user_id,
                    'Total Spending': analysis.get('total_spending', 0),
                    'Transactions': analysis.get('total_transactions', 0),
                    'Avg Transaction': analysis.get('average_transaction_amount', 0),
                    'Unique Merchants': analysis.get('unique_merchants', 0)
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            
            # Comparison chart
            fig = px.bar(comparison_df, x='User', y='Total Spending', 
                        title="Total Spending Comparison Across Users")
            st.plotly_chart(fig, use_container_width=True)
            
            # Comparison table
            st.dataframe(comparison_df, use_container_width=True)
    
    else:
        # Welcome message
        st.markdown("""
        ### 🎯 Welcome to Financial Agent!
        
        This application analyzes your transaction data and provides:
        - **📊 Detailed spending analysis** for each user
        - **🤖 AI-powered financial insights** using advanced language models
        - **📈 Interactive visualizations** of spending patterns
        - **👥 Multi-user comparison** capabilities
        
        **Getting Started:**
        1. Upload your transaction file (Excel/CSV) or use sample data
        2. Click "Analyze Transactions" to start the analysis
        3. Explore individual user profiles and insights
        4. Compare spending patterns across users
        
        **Sample Data Included:**
        The app comes with sample UPI transaction data for 3 users with 844+ transactions.
        """)

if __name__ == "__main__":
    main()