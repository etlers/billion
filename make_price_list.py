import pandas as pd
import numpy as np

df_price = pd.read_csv("./csv/agreement.csv")
df_price = df_price.loc[df_price["date"].astype(str) == "20210402"]
df_price = df_price.sort_values(by=["date","time"])
list_price = list(np.array(df_price["price"].tolist()))
print(list_price)