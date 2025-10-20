import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timezone
from scipy.interpolate import UnivariateSpline, Rbf

'''
We intend to create a 3D plot of the option's volatility surface.
1) The x-axis will show us the strike price
2) The y-axis will serve as the time till expiration
3) the z-axis will respresnt the implied volatility

we will have toggles to switch between calls and puts
'''

ticker = 'SPY'  # options include SPY, QQQ, AAPL, MSFT, GOOGL
max_days = 365
max_implied_volatility = 3.0
min_bid = 0.01
min_open_interest = 5

stock_data = yf.Ticker(ticker)
spot = stock_data.fast_info["last_price"]  # Store current price

# List available expiration dates
expirations = []

expirations = []
for expiration in stock_data.options:
    d = datetime.strptime(expiration, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if (d - datetime.now(timezone.utc)).days > 0 and (d - datetime.now(timezone.utc)).days <= max_days:
        expirations.append(expiration)

def percentage_of_year(d):
    return max((d - datetime.now(timezone.utc)).days, 1) / 365.0

datapoints = []

for expiration in expirations:
    chain = stock_data.option_chain(expiration)
    d = datetime.strptime(expiration, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    T = percentage_of_year(d)

    # Only use calls when Strike >= Spot, puts when Strike <= Spot to avoid deep ITM noise
    calls = chain.calls.copy()
    puts = chain.puts.copy()

    calls = calls[(calls["strike"] >= spot)]
    puts = puts[(puts["strike"] <= spot)]

    # combine and clean
    df = pd.concat([calls.assign(side="C"), puts.assign(side="P")], ignore_index=True)

    # liquidity filters
    df = df[(df["bid"] >= min_bid) & (df["openInterest"] >= min_open_interest)]
    # prefer yfinance IV if present and valid
    df = df[np.isfinite(df["impliedVolatility"])]
    df = df[(df["impliedVolatility"] > 0) & (df["impliedVolatility"] < max_implied_volatility)]

    if df.empty:
        continue

    # transform axes to log-moneyness and time to expiry
    strike = df["strike"].values.astype(float)
    logMoneyness = np.log(strike / spot)
    impliedVolatility = df["impliedVolatility"].values.astype(float)

    try:
        spline = UnivariateSpline(logMoneyness, impliedVolatility, s=0.0005)
        grid_logMoneyness = np.linspace(logMoneyness.min(), logMoneyness.max(), 50)
        grid_impliedVolatility = spline(grid_logMoneyness)
    except Exception:
        grid_logMoneyness, grid_impliedVolatility = logMoneyness, impliedVolatility

    T_expirations = np.full_like(grid_impliedVolatility, T, dtype=float)

    for x, y, z in zip(grid_logMoneyness, T_expirations, grid_impliedVolatility):
        datapoints.append((x, y, z))

points = np.array(datapoints)
x_points, y_points, z_points = points[:,0], points[:,1], points[:,2]

weights = (z_points ** 2) * y_points

# define rectangular grid
x_grid = np.linspace(np.percentile(x_points, 5), np.percentile(x_points, 95), 80)   # log-moneyness range
y_grid = np.linspace(y_points.min(), y_points.max(), 40)                            # maturities in years
X_grid, Y_grid = np.meshgrid(x_grid, y_grid)

# set an epsilon scaled to data spread and a small smoothing factor to flatten "fins"
epsilon = 0.5 * np.sqrt(np.var(x_points) + np.var(y_points))
rbf = Rbf(x_points, y_points, weights, function="multiquadric", epsilon=epsilon, smooth=0.001)
Weights = rbf(X_grid, Y_grid)

# compute implied vol back from total variance
Z_points = np.sqrt(np.maximum(Weights / np.maximum(Y_grid, 1*10**-6), 0))
Z_points = np.ma.masked_invalid(Z_points)

# plot
fig = go.Figure(data=[go.Surface(z=Z_points, x=X_grid, y=Y_grid, colorscale="Plasma")])
fig.update_layout(
    title=f"{ticker} Implied Volatility Surface (OTM, log-moneyness vs years)",
    scene=dict(
        xaxis_title="log-moneyness ln(Strike/Spot)",
        yaxis_title="Time to Expiry (years)",
        zaxis_title="Implied Volatility"
    ),
    template="plotly_dark"
)

fig.show()