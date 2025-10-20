import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timezone
from scipy.interpolate import UnivariateSpline, Rbf
import os
from glob import glob

'''
We intend to create a 3D plot of the option's volatility surface.
1) The x-axis will show us the strike price
2) The y-axis will serve as the time till expiration
3) the z-axis will respresnt the implied volatility

we will have toggles to switch between calls and puts
'''

ticker = 'SPY'  # options include TSLA, SPY, QQQ, AAPL, MSFT, GOOGL
max_days = 365
max_implied_volatility = 3.0
min_bid = 0.01
min_open_interest = 5

snapshot_dir = "./data/snapshots"
latest_file = max(glob(os.path.join(snapshot_dir, f"{ticker}_*.csv")), key=os.path.getmtime)
print(f"Loading snapshot → {latest_file}")
df = pd.read_csv(latest_file)
spot = float(df["spot"].iloc[0])  # same as live version
r, q = 0.05, 0.015

def percentage_of_year(exp):
    d = datetime.strptime(str(exp), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return max((d - datetime.now(timezone.utc)).days, 1) / 365.0

datapoints = []

for expiration in df["expiration"].unique():
    chain_df = df[df["expiration"] == expiration]

    T = percentage_of_year(expiration)
    if T < 0.03:
        continue
    F = spot * np.exp((r - q) * T)

    calls = chain_df[chain_df["side"] == "C"].copy()
    puts  = chain_df[chain_df["side"] == "P"].copy()

    # keep out-of-the-money sides
    calls = calls[(calls["strike"] > F * 1.00)]
    puts  = puts[(puts["strike"] < F * 1.00)]

    filtered = pd.concat([calls.assign(side="C"), puts.assign(side="P")], ignore_index=True)

    # --- liquidity filters ---
    filtered = filtered[(filtered["bid"] >= min_bid) & (filtered["openInterest"] >= min_open_interest)]
    filtered = filtered[np.isfinite(filtered["impliedVolatility"])]
    filtered = filtered[(filtered["impliedVolatility"] > 0) & (filtered["impliedVolatility"] < max_implied_volatility)]

    if filtered.empty:
        continue

    strike = filtered["strike"].values.astype(float)
    logMoneyness = np.log(strike / spot)
    impliedVolatility = filtered["impliedVolatility"].values.astype(float)

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
rbf = Rbf(x_points, y_points, weights, function="multiquadric", epsilon=epsilon, smooth=0.0006)
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

W_pred = rbf(x_points, y_points)
Z_pred = np.sqrt(np.maximum(W_pred / np.maximum(y_points, 1e-6), 0))

mae = np.average(np.abs(Z_pred - z_points))
print("Weighted MAE to quotes:", mae)

print("Total points:", len(x_points))
print("neg count (k<0):", np.sum(x_points < 0))
print("pos count (k>0):", np.sum(x_points > 0))
print("ATM band count (|k|<=0.02):", np.sum(np.abs(x_points) <= 0.02))

fig.show()