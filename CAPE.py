from akshare import (
    stock_profit_sheet_by_report_em,  # 利润表，用于提取 EPS
    stock_zh_a_daily                  # 历史行情，用于获取收盘价
)
import os
import pandas as pd
import numpy as np
# 1. 定义股票列表
symbols = [
    "sz000598","sz000605","sz000685","sz003039",
    "sh600008","sh600168","sh600187","sh600283",
    "sh600461","sh600769","sh601158","sh601199",
    "sh601368","sh603291","sh603759",
]

# 2. 确保 data 目录存在
if not os.path.exists("data"):
    os.makedirs("data")

results = []

for stock in symbols:
    # 3. 拉取／加载利润表，提取 “BASIC_EPS”
    inc_path = f"data/{stock}_利润表.csv"
    if not os.path.exists(inc_path):
        df_inc = stock_profit_sheet_by_report_em(symbol=stock).fillna(0)
        df_inc.to_csv(inc_path, encoding="utf-8", index=False)
    else:
        df_inc = pd.read_csv(inc_path, encoding="utf-8")
    # —— 修改开始 —— #
    # 把 REPORT_DATE 转为 datetime，排序
    df_inc["REPORT_DATE"] = pd.to_datetime(df_inc["REPORT_DATE"])
    df_inc = df_inc.sort_values("REPORT_DATE")
    # 按年度分组，取 BASIC_EPS 的平均值
    df_inc["year"] = df_inc["REPORT_DATE"].dt.year
    eps_yearly = df_inc.groupby("year")["BASIC_EPS"].mean()
    # 取最近 10 年（若不足 10 年则取全部）
    eps_10y = eps_yearly.tail(10)
    avg_eps_10y = eps_10y.mean()
    # —— 修改结束 —— #

    # 4. 拉取／加载历史行情，取最新收盘价
    symbol_code = int(stock.replace("sz", "").replace("sh", ""))
    prefix = "SZ" if stock.startswith("sz") else "SH"
    daily_path = f"data/{stock}_行情.csv"
    if not os.path.exists(daily_path):
        df_price = stock_zh_a_daily(symbol=stock, adjust="")
        df_price.to_csv(daily_path, encoding="utf-8", index=False)
    else:
        df_price = pd.read_csv(daily_path, encoding="utf-8", parse_dates=["date"])
    latest_close = df_price.sort_values("date").iloc[-1]["close"]

    # 5. 计算席勒市盈率（CAPE）
    cape = latest_close / avg_eps_10y if avg_eps_10y != 0 else float("nan")

    results.append({
        "stock": stock,
        "最新收盘价": latest_close,
        "十年平均EPS": avg_eps_10y,
        "席勒市盈率(CAPE)": cape
    })

df_res = pd.DataFrame(results)

# 将 NaN 的 CAPE 看作极大值，避免排在最前
df_res["席勒市盈率(CAPE)"] = df_res["席勒市盈率(CAPE)"].astype(float)

# 按 CAPE 升序排序（CAPE 越低越有价值）
df_sorted = df_res.sort_values(
    by="席勒市盈率(CAPE)",
    key=lambda x: x.fillna(np.inf)
).reset_index(drop=True)

# # 保存排序结果
# sorted_path = "data/15只股票_CAPE价值排序.csv"
# df_sorted.to_csv(sorted_path, encoding="utf-8", index=False)

# 输出排序后的 DataFrame
print(df_sorted)