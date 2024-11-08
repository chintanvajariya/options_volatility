import yfinance as yf
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt

# Define the ticker symbol and fetch data
ticker = 'DJT'
stock_data = yf.Ticker(ticker)

# List available expiration dates
expirations = stock_data.options
print("Available Expiration Dates:", expirations)

# Choose an expiration date
chosen_expiration = expirations[10]  # Choose the first expiration date as an example

# Fetch the option chain for the chosen expiration date
option_chain = stock_data.option_chain(chosen_expiration)
calls = option_chain.calls
puts = option_chain.puts

# Extract strike prices and last prices for calls and puts
# Find common strike prices between calls and puts
common_strikes = calls.merge(puts, on='strike', suffixes=('_call', '_put'))
strike_prices = common_strikes['strike']
call_prices = common_strikes['lastPrice_call']
put_prices = common_strikes['lastPrice_put']

plt.figure(figsize=(10, 6))
plt.plot(strike_prices, call_prices, label="Call Option Price", color="blue")
plt.plot(strike_prices, put_prices, label="Put Option Price", color="red")
plt.xlabel("Strike Price")
plt.ylabel("Option Price")
plt.title(f"Real-Life Call and Put Option Prices vs. Strike Prices ({ticker}) - Expiration: {chosen_expiration}")
plt.legend()
plt.grid(True)
plt.show()