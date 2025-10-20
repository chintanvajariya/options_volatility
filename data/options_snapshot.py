import yfinance as yf
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytz
import os

TICKER = "SPY"
SNAPSHOT_DIR = "./data/snapshots"
TARGET_HOUR_ET = 10
TARGET_MINUTE_ET = 45

def next_snapshot_time():
    now = datetime.now(pytz.timezone("US/Eastern"))
    target = now.replace(hour=TARGET_HOUR_ET, minute=TARGET_MINUTE_ET, second=0, microsecond=0)
    if now > target:
        target += timedelta(days=1)
    return target

def save_option_snapshot(ticker=TICKER):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    stock = yf.Ticker(ticker)
    spot = stock.fast_info["last_price"]

    timestamp = datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d_%H-%M-%S_ET")
    all_data = []

    for expiration in stock.options:
        try:
            exp_date = datetime.strptime(expiration, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_out = (exp_date - datetime.now(timezone.utc)).days
            if days_out < 0 or days_out > 365:
                continue

            chain = stock.option_chain(expiration)
            calls = chain.calls.copy()
            puts = chain.puts.copy()

            # Add uniform columns used by our visualizer
            for df, side in [(calls, "C"), (puts, "P")]:
                df["side"] = side
                df["expiration"] = expiration
                df["spot"] = spot
                df["timestamp"] = timestamp

            all_data.append(pd.concat([calls, puts], ignore_index=True))

        except Exception as e:
            print(f"Error fetching {expiration}: {e}")

    if not all_data:
        return

    df = pd.concat(all_data, ignore_index=True)

    # Keep only columns required by visualizer
    keep_cols = [
        "side",
        "expiration",
        "strike",
        "bid",
        "openInterest",
        "impliedVolatility",
        "spot",
        "timestamp",
    ]
    df = df[[c for c in keep_cols if c in df.columns]]

    # Clean & normalize
    df = df.dropna(subset=["strike", "impliedVolatility"])
    df["strike"] = df["strike"].astype(float)
    df["bid"] = df["bid"].fillna(0).astype(float)
    df["openInterest"] = df["openInterest"].fillna(0).astype(int)
    df["impliedVolatility"] = df["impliedVolatility"].astype(float)
    df["spot"] = float(spot)

    # Save snapshot
    fname = f"{SNAPSHOT_DIR}/{ticker}_{timestamp}.csv"
    df.to_csv(fname, index=False)

# ---------- MAIN ----------
if __name__ == "__main__":
    print(f"Starting snapshot for {TICKER} at {datetime.now(pytz.timezone("US/Eastern")).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    save_option_snapshot()
