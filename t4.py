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
    signal[(signal["fear"] < 15) & (signal["High"] > 30)]["date"]
)

# ========= 2. SOXL =========
soxl = pd.read_csv(
    "TQQQ_2011-01-06__2026-04-18_stock_data.csv",
    skiprows=[1,2]
)

soxl["Date"] = pd.to_datetime(soxl["Price"])
soxl = soxl.sort_values("Date").reset_index(drop=True)
price_map = soxl.set_index("Date")

# ========= 3. 回测 =========
cash = 100.0
position = 0  # 0=空仓, 1=持仓

entry_price = 0
entry_date = None

trades = []

for i in range(len(soxl)):

    row = soxl.iloc[i]
    date = row["Date"]

    # ========= 空仓状态：只允许第一次信号买入 =========
    if position == 0:
        if date in signal_dates:
            entry_price = row["Open"]
            entry_date = date
            position = 1
            continue

    # ========= 持仓状态 =========
    if position == 1:
        # 止盈条件
        if row["Close"] >= entry_price * 2:

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

            # 平仓 → 回到空仓
            position = 0
            entry_price = 0
            entry_date = None

# ========= 输出 =========
df_trades = pd.DataFrame(trades)

print(df_trades)
print("\nFinal Capital:", cash)

df_trades.to_csv("tqqq_trade_log_stateful.csv", index=False)