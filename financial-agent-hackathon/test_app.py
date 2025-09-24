"""
Test script to verify the Streamlit app functionality
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.getcwd())

from utils.data_loader import load_transactions
from main_refactored import load_and_analyze_for_streamlit

def test_data_loading():
    """Test data loading and column checking"""
    print("Testing data loading...")
    
    # Load data
    df = load_transactions("sample_data/upi_transactions.xlsx")
    if df is None:
        print("❌ Failed to load data")
        return False
    
    print(f"✅ Data loaded successfully. Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Test analysis
    print("\nTesting analysis...")
    try:
        full_df, results = load_and_analyze_for_streamlit("sample_data/upi_transactions.xlsx")
        if results:
            print(f"✅ Analysis completed for {len(results)} users")
            
            # Check first user's data structure
            first_user = list(results.keys())[0]
            user_data = results[first_user]
            print(f"\nUser {first_user} data keys: {list(user_data.keys())}")
            
            if 'pandas_analysis' in user_data:
                analysis = user_data['pandas_analysis']
                print(f"Analysis keys: {list(analysis.keys())}")
                
            return True
        else:
            print("❌ No analysis results")
            return False
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

if __name__ == "__main__":
    success = test_data_loading()
    if success:
        print("\n🎉 All tests passed! The app should work correctly.")
    else:
        print("\n❌ Tests failed. Please check the errors above.")