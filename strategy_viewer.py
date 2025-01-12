import streamlit as st
import pandas as pd
import json  # Use json for parsing instead of eval()

# Load the data files
@st.cache
def load_data():
    strategy_levels_path = "/content/sample_data/strategy_levels_aligned.csv"
    portfolio_decomposition_path = "/content/sample_data/portfolio_decomposition_aligned.csv"

    strategy_levels = pd.read_csv(strategy_levels_path)
    portfolio_decomposition = pd.read_csv(portfolio_decomposition_path)

    # Convert date columns to datetime
    strategy_levels['Date'] = pd.to_datetime(strategy_levels['Date'])
    portfolio_decomposition['date'] = pd.to_datetime(portfolio_decomposition['date'])

    # Merge datasets
    merged_data = pd.merge(
        strategy_levels, portfolio_decomposition, left_on='Date', right_on='date', how='inner'
    )
    merged_data.drop(columns=['date'], inplace=True)
    return merged_data

# Load the data
merged_data = load_data()

# Streamlit App
st.title("Options Strategy Viewer")

# Date input
selected_date = st.date_input(
    "Select a date to view the strategy details:",
    value=merged_data['Date'].min(),
    min_value=merged_data['Date'].min(),
    max_value=merged_data['Date'].max()
)

# Filter data based on the selected date
data_for_date = merged_data[merged_data['Date'] == pd.Timestamp(selected_date)]

if not data_for_date.empty:
    # Display Strategy Level
    strategy_level = data_for_date.iloc[0]['Strategy Level']
    st.subheader(f"Strategy Level: {strategy_level:.2f}")

    # Extract call and put positions
    call_positions = data_for_date['call_positions'].iloc[0]
    put_positions = data_for_date['put_positions'].iloc[0]

    try:
        # Use json.loads() to parse JSON strings safely
        call_positions_df = pd.DataFrame(json.loads(call_positions))
        put_positions_df = pd.DataFrame(json.loads(put_positions))
    except json.JSONDecodeError:
        st.error("Error parsing call or put positions. Ensure they are in a valid JSON format.")
        st.stop()

    # Select columns to display
    columns_to_display = ['strike', 'delta', 'maturity', 'units']

    st.subheader("Call Options")
    st.table(call_positions_df[columns_to_display])

    st.subheader("Put Options")
    st.table(put_positions_df[columns_to_display])

    # Display underlying delta
    underlying_delta = data_for_date.iloc[0]['underlying_delta']
    st.subheader(f"Underlying Delta: {underlying_delta:.2f}")
else:
    st.warning("No data available for the selected date.")

