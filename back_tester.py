import pandas as pd
import numpy as np
from scipy.stats import norm

# Preprocess data by renaming columns and computing Vega
def preprocess_data(data):
    data.rename(columns={'ImpliedVol': 'sigma'}, inplace=True)
    data['StrikeDiff'] = 0  # Placeholder for strike difference
    data['Vega'] = data.apply(compute_vega, axis=1)
    return data

# Compute Vega for options using Black-Scholes
def compute_vega(row):
    S = row['UnderlyingPrice']
    K = row['Strike']
    T = row['T']
    sigma = row['sigma']
    r = 0  # Assuming a risk-free rate of 0 for simplicity

    if T > 0:
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        return S * norm.pdf(d1) * np.sqrt(T)
    return 0

# Calculate Delta and Vega for an option
def black_scholes_greeks(S, K, T, r, sigma, option_type):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'call':
        delta = norm.cdf(d1)
    else:  # put
        delta = -norm.cdf(-d1)

    vega = S * norm.pdf(d1) * np.sqrt(T)
    return delta, vega

# Select appropriate options
def select_options(data_group, underlying_level, current_date):
    data_group['StrikeDiff'] = abs(data_group['Strike'] - underlying_level)
    filtered_data = data_group[data_group['Maturity'] > current_date]
    expiries = sorted(filtered_data['Maturity'].unique())

    if len(expiries) >= 3:
        third_maturity_date = expiries[2]
        options = filtered_data[filtered_data['Maturity'] == third_maturity_date]
        call_option = options[options['OptionType'] == 'Call']
        put_option = options[options['OptionType'] == 'Put']

        if not call_option.empty and not put_option.empty:
            return call_option.iloc[0], put_option.iloc[0]

    return None, None

# Calculate the strategy level
def calculate_strategy_level(prev_strategy, portfolio, underlying_change):
    option_contribution = sum(
        opt['units'] * (opt['price_t'] - opt['price_t_1']) for opt in portfolio
    )
    delta_contribution = sum(opt['delta'] * opt['units'] for opt in portfolio)
    return prev_strategy + option_contribution + delta_contribution * underlying_change

# Backtesting logic
def backtest_strategy(data, start_strategy_level=100, end_date=pd.Timestamp("2024-06-28")):
    data['Maturity'] = pd.to_datetime(data['ExpiryDate'])
    data['AsOfDate'] = pd.to_datetime(data['AsOfDate'])
    data['T'] = (data['Maturity'] - data['AsOfDate']).dt.days / 365

    data = preprocess_data(data)

    strategy_levels = [start_strategy_level]
    portfolio_decomposition = []

    unique_dates = data['AsOfDate'].unique()
    unique_dates = unique_dates[unique_dates <= end_date]

    portfolio = []

    for idx, current_date in enumerate(unique_dates):
        current_data = data[data['AsOfDate'] == current_date]

        if idx == 0:
            # Initialize portfolio on the first day
            underlying_level = current_data['UnderlyingPrice'].iloc[0]
            call, put = select_options(current_data, underlying_level, current_date)

            if call is not None and put is not None:
                portfolio.append({'OptionType': 'Call', 'delta': call['delta'], 'units': 1, **call})
                portfolio.append({'OptionType': 'Put', 'delta': put['delta'], 'units': 1, **put})

        strategy_level = calculate_strategy_level(
            strategy_levels[-1], portfolio, current_data['UnderlyingPrice'].iloc[0]
        )
        strategy_levels.append(strategy_level)

    return strategy_levels, portfolio_decomposition
