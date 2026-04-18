import yfinance as yf

vix = yf.download("^VIX", start="2000-01-01")
print(vix.head())

vix.to_csv("vix.csv")