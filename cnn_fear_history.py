import pandas as pd
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Referer': 'https://www.finhacker.cz/fear-and-greed-index-historical-data-and-chart/',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Priority': 'u=4',
    # Requests doesn't support trailers
    # 'TE': 'trailers',
}

response = requests.get('https://www.finhacker.cz/wp-content/custom-api/fear-greed-data.php', headers=headers)
data=(response.json()['daily'])
df = pd.DataFrame(data)
df.to_csv("fear_greed_index.csv", index=False)
print("数据已保存到 fear_greed_index.csv")