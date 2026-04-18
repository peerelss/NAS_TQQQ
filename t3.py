import pandas as pd

df = pd.read_csv("fear.csv")
result = df[df["fear"] < 15]
print(result)
result.to_csv("fear_extreme_days.csv", index=False)