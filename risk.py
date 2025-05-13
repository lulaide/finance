import numpy as np
import pandas as pd
import akshare as ak

#获取数据  
df=ak.stock_zh_index_daily('sz000598')
df['date'] = pd.to_datetime(df.date)
df = df.set_index('date')
returns=df.close.pct_change().dropna()  



# 置信水平为 95%  
confidence_level = 0.95  
# 时间窗口（以天为单位）  
time_period = 5  # 一周有5个交易日  
# 计算一周的累积收益率  
cumulative_returns = (1 + returns).rolling(window=time_period).apply(np.prod) - 1  
# 计算在1 - 置信水平（这里是5%）处的分位数  
VaR2 = np.percentile(cumulative_returns.dropna(), 100 * (1 - confidence_level))  
print(f"在{confidence_level * 100}%的置信水平下，一周的价值在险（VaR）为：{VaR2:.4f}")  

