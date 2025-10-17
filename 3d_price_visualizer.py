import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

'''
We intend to create a 3D plot of the option's volatility surface.
1) The x-axis will show us the strike price
2) The y-axis will serve as the time till expiration
3) the z-axis will respresnt the implied volatility

we will have toggles to switch between calls and puts
'''

ticker = 'SPY'  # Other high-liquidity tickers include AAPL QQQ TSLA SPY
date = 0  # Chosen index for expiration date
rate = 0.0443  # Risk-free rate

stock_data = yf.Ticker(ticker)
price = stock_data.history_metadata['regularMarketPrice']  # Store current price


# List available expiration dates
expirations = stock_data.options

first_expiration = expirations[0]
first_exp_date = datetime.strptime(first_expiration, '%Y-%m-%d')
cutoff_date = first_exp_date + timedelta(days=365)

filtered_expirations = []
for exp in expirations:
    exp_date = datetime.strptime(exp, '%Y-%m-%d')
    if exp_date <= cutoff_date:
        filtered_expirations.append(exp)

expirations = filtered_expirations

# Fetch the option chain for the chosen expiration date
option_chain, calls, puts = [], [], []

for expiration in expirations:
    option_chain.append(stock_data.option_chain(expiration))
    calls.append(option_chain[expirations.index(expiration)].calls)
    puts.append(option_chain[expirations.index(expiration)].puts)


# x axis is strikes
strikes = []             # x axis
expirations              # y axis
implied_volatility = []  # z axis

# Filter out extreme IVs (keep only IV <= 1.0)
max_iv = 1.0

for call in calls:
    strikes.append(call['strike'])

for call in calls:
    implied_volatility.append(call['impliedVolatility'])

# Apply IV filtering while maintaining data structure
for i in range(len(implied_volatility)):
    for j in range(len(implied_volatility[i])):
        if implied_volatility[i][j] > max_iv:
            implied_volatility[i][j] = np.nan

fig = go.Figure(data=[go.Surface(z=implied_volatility, x=strikes, y=expirations)])
fig.update_layout(
    xaxis_title="Strikes",
    yaxis_title="Expirations",
    # zaxis_title="Implied Volatility"
)

fig.show()