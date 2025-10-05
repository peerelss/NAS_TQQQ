import yfinance as yf

# 指定股票代码和时间范围
ticker = "^IXIC"  # 替换成您感兴趣的股票代码
start_date = "1985-03-03"  # 替换成您感兴趣的起始日期
end_date = "2025-10-03"  # 替换成您感兴趣的结束日期

# 获取历史股票价格数据
stock_data = yf.download(ticker, start=start_date, end=end_date)
stock_data.to_csv(ticker+"_stock_data.csv")

print(f"已保存为 {ticker}stock_data.csv")
