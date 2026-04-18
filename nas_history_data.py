import yfinance as yf

# 指定股票代码和时间范围
ticker = "TQQQ"  # 替换成您感兴趣的股票代码
start_date = "2011-01-06"  # 替换成您感兴趣的起始日期
end_date = "2026-04-18"  # 替换成您感兴趣的结束日期
filename = f"{ticker}_{start_date}__{end_date}_stock_data.csv"
# 获取历史股票价格数据
stock_data = yf.download(ticker, start=start_date, end=end_date)
stock_data.to_csv(filename)

print(f"已保存为{filename}")
