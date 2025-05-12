from akshare import stock_cash_flow_sheet_by_report_em, stock_zh_a_spot_em
import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import matplotlib

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体

# 1. 读取或拉取现金流数据
stock = "sz000598"
csv_path = f"data/{stock}_现金流.csv"
if not os.path.exists(csv_path):
    df_cf = stock_cash_flow_sheet_by_report_em(symbol=stock)
    df_cf.to_csv(csv_path, encoding="utf-8", index=False)
else:
    df_cf = pd.read_csv(csv_path, encoding="utf-8")

# 2. 计算 FCF
df_fc = df_cf[["REPORT_DATE", "NETCASH_OPERATE", "CONSTRUCT_LONG_ASSET"]].copy()
df_fc["REPORT_DATE"] = pd.to_datetime(df_fc["REPORT_DATE"])
df_fc = df_fc.sort_values("REPORT_DATE")
df_fc["FCF"] = df_fc["NETCASH_OPERATE"] - df_fc["CONSTRUCT_LONG_ASSET"]

# 3. 筛选每年年末（12 月）数据
df_year_end = df_fc[df_fc["REPORT_DATE"].dt.month == 12].sort_values("REPORT_DATE")

# 4. 准备特征 X=年份，标签 y=FCF
years = df_year_end["REPORT_DATE"].dt.year.values.reshape(-1, 1)
fcf = df_year_end["FCF"].values

# 5. 训练线性回归模型
model = LinearRegression()
model.fit(years, fcf)

# 6. 预测未来 3 年的 FCF
last_year = df_year_end["REPORT_DATE"].dt.year.max()
future_years = np.array([last_year + i for i in range(1, 4)]).reshape(-1, 1)
fcf_forecast = model.predict(future_years)

# 7. 用 DCF 函数计算企业价值
def calc_dcf(fcf_forecast, wacc, g):
    pv_fcf = sum(cf / (1 + wacc)**(i+1) for i, cf in enumerate(fcf_forecast))
    terminal_value = fcf_forecast[-1] * (1 + g) / (wacc - g)
    pv_terminal = terminal_value / (1 + wacc)**len(fcf_forecast)
    return pv_fcf + pv_terminal

wacc = 0.08  # 折现率 8%
g = 0.04     # 永续增长率 4%
ev = calc_dcf(fcf_forecast, wacc, g)

# 8. 获取当前总市值（单位：亿元），并换算成元
df_spot = stock_zh_a_spot_em()
symbol_code = stock.replace("sz", "")
market_cap_yi = float(df_spot.loc[df_spot["代码"] == symbol_code, "总市值"].values[0])
market_cap = market_cap_yi * 1e8  # 换算为元

# 9. 输出对比结果
print("历史年末 FCF：", dict(zip(df_year_end["REPORT_DATE"].dt.year, df_year_end["FCF"])))
print("预测未来三年 FCF：", dict(zip(future_years.flatten(), fcf_forecast)))
print(f"DCF 模型估算企业价值 (EV): {ev:,.2f} 元")
print(f"当前总市值: {market_cap:,.2f} 元")
print(f"估值/市值 比率: {ev/market_cap:.2f}")

# 10. 可视化历史与预测 FCF
years_hist = df_year_end["REPORT_DATE"].dt.year.values
fcf_hist = df_year_end["FCF"].values
# 准备预测点
years_pred = future_years.flatten()
fcf_pred = fcf_forecast

plt.figure(figsize=(8, 4))
plt.plot(years_hist, fcf_hist, marker='o', linestyle='-', label='历史 FCF')
plt.plot(years_pred, fcf_pred, marker='o', linestyle='--', label='预测 FCF')
plt.xlabel('年份')
plt.ylabel('自由现金流 (元)')
plt.title('贵州茅台 历史与预测自由现金流')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()