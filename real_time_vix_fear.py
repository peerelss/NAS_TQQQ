import requests
import yfinance as yf
import time
from datetime import datetime

FG_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

def get_fear_greed():
    try:
        res = requests.get(FG_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        data = res.json()
        score = data['fear_and_greed']['score']
        rating = data['fear_and_greed']['rating']
        return score, rating
    except Exception as e:
        return None, str(e)

def get_vix():
    try:
        vix = yf.Ticker("^VIX")
        # 取最近1分钟数据
        data = vix.history(period="1d", interval="1m")
        if not data.empty:
            last = data.iloc[-1]
            return float(last["Close"])
        return None
    except Exception as e:
        return None

# 🔁 实时循环
while True:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    fg_score, fg_rating = get_fear_greed()
    vix_value = get_vix()

    print(f"[{now}]")
    print("Fear & Greed:", fg_score, fg_rating)
    print("VIX:", vix_value)
    print("-" * 40)

    time.sleep(60*5)  # 每分钟更新