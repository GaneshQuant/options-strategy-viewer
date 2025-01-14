import pandas as pd
import numpy as np
from scipy.stats import norm

def preprocess_data(data):
    """Preprocess the dataset to include necessary calculations upfront."""
    data.rename(columns={'ImpliedVol': 'sigma'}, inplace=True)
    data['StrikeDiff'] = 0  # Placeholder for strike difference
    data['Vega'] = data.apply(compute_vega, axis=1)
    return data

def compute_vega(row):
    S = row['UnderlyingPrice']
    K = row['Strike']
    T = row['T']
    sigma = row['sigma']
    r = 0  # Assuming risk-free rate is 0 for simplicity

    if T > 0:  # Ensure T > 0 to avoid division errors
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        return S * norm.pdf(d1) * np.sqrt(T)
    return 0

def black_scholes_greeks(S, K, T, r, sigma, option_type):
    """Calculates Delta and Vega for the Black-Scholes model."""
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'call':
        delta = norm.cdf(d1)
    else:  # put
        delta = -norm.cdf(-d1)

    vega = S * norm.pdf(d1) * np.sqrt(T)
    return delta, vega

def select_options(data_group, underlying_level, current_date):
    """Select call and put options for the given data group."""
    data_group['StrikeDiff'] = abs(data_group['Strike'] - underlying_level)
    sorted_group = data_group.sort_values(by=['StrikeDiff', 'Strike'])
    filtered_data = sorted_group[sorted_group['Maturity'] > current_date]
    expiries = sorted(filtered_data['Maturity'].unique())

    if len(expiries) >= 3:
        third_maturity_date = expiries[2]
        third_maturity_options = filtered_data[filtered_data['Maturity'] == third_maturity_date]
        call_option = third_maturity_options[third_maturity_options['OptionType'] == 'Call']
        put_option = third_maturity_options[third_maturity_options['OptionType'] == 'Put']

        if not call_option.empty and not put_option.empty:
            return call_option.iloc[0], put_option.iloc[0]

    return None, None

def calculate_vega_weighting(call_option, put_option, strategy_level, is_new_option):
    vega_weight = 0.015873 / 100
    vega_call = call_option['Vega']
    vega_put = put_option['Vega']

    if is_new_option:
        if vega_call + vega_put > 0:
            units_option = -100 * vega_weight * strategy_level / (vega_call + vega_put)
            return units_option
    return None

def delta_hedging(portfolio):
    """Delta hedging using Black-Scholes logic for all options in the portfolio."""
    delta_total = 0
    for option in portfolio:
        delta_option = option['delta'] * option['units']
        delta_total += delta_option
    return delta_total

def calculate_strategy_level(prev_strategy, portfolio, underlying_change):
    """Calculate the new strategy level based on the portfolio and underlying movements."""
    option_contribution = sum(
        option['units'] * (option['price_t'] - option['price_t_1'])
        for option in portfolio
    )
    delta_units = delta_hedging(portfolio)
    underlying_contribution = delta_units * underlying_change
    return prev_strategy + option_contribution + underlying_contribution

def backtest_strategy_aligned(data, start_strategy_level=100, end_date=pd.Timestamp("2024-06-28")):
    strategy_levels = [start_strategy_level]
    portfolio_decomposition = []

    unique_dates = data['AsOfDate'].unique()
    unique_dates = unique_dates[unique_dates <= end_date]

    # Initialize the portfolio with positions for the first day
    portfolio = []

    # Process the first day explicitly
    first_date = unique_dates[0]
    first_day_data = data[data['AsOfDate'] == first_date]
    underlying_level = first_day_data['UnderlyingPrice'].iloc[0]

    # Select options for the first day
    call, put = select_options(first_day_data, underlying_level, first_date)
    if call is not None and put is not None:
        call_delta, call_vega = black_scholes_greeks(
            underlying_level, call['Strike'], call['T'], 0, call['sigma'], 'call'
        )
        put_delta, put_vega = black_scholes_greeks(
            underlying_level, put['Strike'], put['T'], 0, put['sigma'], 'put'
        )
        portfolio = [
            {'delta': call_delta, 'units': calculate_vega_weighting(call, put, start_strategy_level, True),
             'strike': call['Strike'], 'maturity': call['Maturity'],
             'price_t': call['Price'], 'price_t_1': call['Price'], 'OptionType': 'Call'},
            {'delta': put_delta, 'units': calculate_vega_weighting(call, put, start_strategy_level, True),
             'strike': put['Strike'], 'maturity': put['Maturity'],
             'price_t': put['Price'], 'price_t_1': put['Price'], 'OptionType': 'Put'}
        ]

    portfolio_snapshot = {
        'date': first_date,
        'call_positions': [opt for opt in portfolio if opt['OptionType'] == 'Call'],
        'put_positions': [opt for opt in portfolio if opt['OptionType'] == 'Put'],
        'underlying_delta': delta_hedging(portfolio)
    }
    portfolio_decomposition.append(portfolio_snapshot)

    # Process subsequent days
    for idx in range(1, len(unique_dates)):
        previous_date = unique_dates[idx - 1]
        current_date = unique_dates[idx]

        previous_data = data[data['AsOfDate'] == previous_date]
        current_data = data[data['AsOfDate'] == current_date]

        if previous_data.empty or current_data.empty:
            strategy_levels.append(strategy_levels[-1])
            continue

        underlying_level = previous_data['UnderlyingPrice'].iloc[0]
        current_underlying_price = current_data['UnderlyingPrice'].iloc[0]

        current_data['StrikeDiff'] = abs(current_data['Strike'] - underlying_level)
        sorted_options = current_data.sort_values(by=['StrikeDiff', 'Strike'])

        call, put = select_options(sorted_options, underlying_level, current_date)

        if call is None or put is None:
            strategy_levels.append(strategy_levels[-1])
            continue

        call_delta, call_vega = black_scholes_greeks(
            underlying_level, call['Strike'], call['T'], 0, call['sigma'], 'call'
        )
        put_delta, put_vega = black_scholes_greeks(
            underlying_level, put['Strike'], put['T'], 0, put['sigma'], 'put'
        )

        # Update portfolio for the current day
        portfolio = [
            {'delta': call_delta, 'units': calculate_vega_weighting(call, put, strategy_levels[-1], True),
             'strike': call['Strike'], 'maturity': call['Maturity'],
             'price_t': call['Price'], 'price_t_1': call['Price'], 'OptionType': 'Call'},
            {'delta': put_delta, 'units': calculate_vega_weighting(call, put, strategy_levels[-1], True),
             'strike': put['Strike'], 'maturity': put['Maturity'],
             'price_t': put['Price'], 'price_t_1': put['Price'], 'OptionType': 'Put'}
        ]

        # Calculate new strategy level
        strategy_level = calculate_strategy_level(strategy_levels[-1], portfolio, current_underlying_price - underlying_level)
        strategy_levels.append(strategy_level)

        portfolio_snapshot = {
            'date': current_date,
            'call_positions': [opt for opt in portfolio if opt['OptionType'] == 'Call'],
            'put_positions': [opt for opt in portfolio if opt['OptionType'] == 'Put'],
            'underlying_delta': delta_hedging(portfolio)
        }
        portfolio_decomposition.append(portfolio_snapshot)

    return strategy_levels, portfolio_decomposition
