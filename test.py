import pandas as pd

# =========================
# 1. 读取 Fear & VIX 信号
# =========================
fear = pd.read_csv("fear.csv")
fear["date"] = pd.to_datetime(fear["date"])
fear["fear"] = fear["fear"].astype(float)

vix = pd.read_csv("vix.csv")
vix["date"] = pd.to_datetime(vix["Price"])
vix["High"] = vix["High"].astype(float)

# VIX 按天聚合
vix_daily = vix.groupby("date")["High"].max().reset_index()

# 合并 fear + vix
signal = pd.merge(fear, vix_daily, on="date", how="inner")

# 筛选极端日期
signal = signal[(signal["fear"] < 15) & (signal["High"] > 30)]

# 只保留日期
signal_dates = signal[["date"]]


# =========================
# 2. 读取 SOXL 数据（跳过脏行）
# =========================
soxl = pd.read_csv(
    "SOXL_2011-01-06__2026-04-18_stock_data.csv",
    skiprows=[1, 2]   # 跳过 Ticker / Date 行
)

soxl["Date"] = pd.to_datetime(soxl["Price"])
soxl["Open"] = soxl["Open"].astype(float)
soxl["Close"] = soxl["Close"].astype(float)

# =========================
# 3. 合并信号日期
# =========================
merged = pd.merge(signal_dates, soxl, left_on="date", right_on="Date", how="inner")

# =========================
# 4. 提取关键字段
# =========================
result = merged[[
    "Date",
    "Open",
    "Close",
    "High",
    "Low",
    "Volume"
]]

print(result)

# 可选保存
result.to_csv("soxl_fear_vix_signals.csv", index=False)