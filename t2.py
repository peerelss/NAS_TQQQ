import pandas as pd

# ========= 1. 信号 =========
fear = pd.read_csv("fear.csv")
fear["date"] = pd.to_datetime(fear["date"])
fear["fear"] = fear["fear"].astype(float)

vix = pd.read_csv("vix.csv")
vix["date"] = pd.to_datetime(vix["Price"])
vix["High"] = vix["High"].astype(float)

vix_daily = vix.groupby("date")["High"].max().reset_index()

signal = pd.merge(fear, vix_daily, on="date")
signal_dates = set(
    signal[
        (signal["fear"] < 10) |
        ((signal["fear"] < 15) & (signal["High"] > 30))
    ]["date"]
)
# ========= 2. SOXL =========
soxl = pd.read_csv(
    "SOXL_2011-01-06__2026-04-18_stock_data.csv",
    skiprows=[1,2]
)

soxl["Date"] = pd.to_datetime(soxl["Price"])
soxl = soxl.sort_values("Date").reset_index(drop=True)
price_map = soxl.set_index("Date")

# ========= 3. 回测 =========
summary_rows = []
multipliers = [i / 10 for i in range(11, 51)]  # 1.1 到 5.0

for multiple in multipliers:
    cash = 100.0
    position = 0  # 0=空仓, 1=持仓
    entry_price = 0
    entry_date = None
    trades = []

    for _, row in soxl.iterrows():
        date = row["Date"]

        if position == 0:
            if date in signal_dates:
                entry_price = row["Open"]
                entry_date = date
                position = 1
                continue

        if position == 1:
            if row["Close"] >= entry_price * multiple:
                exit_price = row["Close"]
                exit_date = date

                ret = exit_price / entry_price
                cash *= ret

                trades.append({
                    "entry_date": entry_date,
                    "entry_price": entry_price,
                    "exit_date": exit_date,
                    "exit_price": exit_price,
                    "return": ret,
                    "capital_after": cash,
                    "hold_days": (exit_date - entry_date).days
                })

                position = 0
                entry_price = 0
                entry_date = None
    
    df_trades = pd.DataFrame(trades)
    print(df_trades)
    print("\nFinal Capital:", cash,"\n")
    df_trades.to_csv("soxl_trade_log_stateful_" + str(multiple) + ".csv", index=False)

    if trades:
        last_trade = trades[-1]
        last_entry_date = last_trade["entry_date"]
        last_entry_price = last_trade["entry_price"]
        last_exit_date = last_trade["exit_date"]
        last_exit_price = last_trade["exit_price"]
    else:
        last_entry_date = None
        last_entry_price = None
        last_exit_date = None
        last_exit_price = None

    summary_rows.append({
        "multiple": multiple,
        "entry_date": last_entry_date,
        "entry_price": last_entry_price,
        "exit_date": last_exit_date,
        "exit_price": last_exit_price,
        "capital_last": cash,
        "trade_count": len(trades)
    })

df_summary = pd.DataFrame(summary_rows)
print(df_summary)
df_summary.to_csv("soxl_trade_log_stateful_summary.csv", index=False)