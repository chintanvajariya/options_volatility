import yfinance as yf
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytz
import os

TICKER = "SPY"
SNAPSHOT_DIR = "./snapshots"
TARGET_HOUR_ET = 10
TARGET_MINUTE_ET = 45

def now_et():
    return datetime.now(pytz.timezone("US/Eastern"))

def next_snapshot_time():
    now = now_et()
    target = now.replace(hour=TARGET_HOUR_ET, minute=TARGET_MINUTE_ET, second=0, microsecond=0)
    if now > target:
        target += timedelta(days=1)
    return target

def save_option_snapshot(ticker=TICKER):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    stock = yf.Ticker(ticker)
    spot = stock.fast_info["last_price"]

    timestamp = now_et().strftime("%Y-%m-%d_%H-%M-%S_ET")
    all_data = []

    for exp in stock.options:
        try:
            chain = stock.option_chain(exp)
            calls = chain.calls.assign(side="call", expiration=exp, spot=spot, timestamp=timestamp)
            puts  = chain.puts.assign(side="put",  expiration=exp, spot=spot, timestamp=timestamp)
            all_data.append(pd.concat([calls, puts]))
        except Exception as e:
            print(f"Error fetching {exp}: {e}")

    if all_data:
        df = pd.concat(all_data, ignore_index=True)
        fname = f"{SNAPSHOT_DIR}/{ticker}_{timestamp}.csv"
        df.to_csv(fname, index=False)

# ---------- MAIN ----------
if __name__ == "__main__":
    print(f"Starting snapshot for {TICKER} at {now_et().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    save_option_snapshot()
