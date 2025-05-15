from akshare import (
    stock_cash_flow_sheet_by_report_em,
    stock_balance_sheet_by_report_em,
    stock_zh_a_spot_em
)
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'PingFang SC', 'Heiti TC', 'Arial Unicode MS', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False  # 正确显示负号

symbols = [
    "sz000598", "sz000605", "sz000685", "sz003039",
    "sh600008", "sh600168", "sh600187", "sh600283",
    "sh600461", "sh600769", "sh601158", "sh601199",
    "sh601368", "sh603291", "sh603759",
]

# --- 0. 缓存实时行情数据，避免每次拉取 ---
os.makedirs('data', exist_ok=True)
spot_path = 'data/实时行情.csv'
if not os.path.exists(spot_path):
    df_spot = stock_zh_a_spot_em()
    df_spot.to_csv(spot_path, encoding='utf-8', index=False)
else:
    df_spot = pd.read_csv(spot_path, encoding='utf-8')

for stock in symbols:
    # --- 1. 读取或拉取并缓存现金流数据 ---
    cf_path = f"data/{stock}_现金流.csv"
    if not os.path.exists(cf_path):
        df_cf = stock_cash_flow_sheet_by_report_em(symbol=stock).fillna(0)
        df_cf.to_csv(cf_path, encoding="utf-8", index=False)
    else:
        df_cf = pd.read_csv(cf_path, encoding="utf-8")

    # --- 2. 计算 FCF 并保留全部期次 ---
    df_cf['REPORT_DATE'] = pd.to_datetime(df_cf['REPORT_DATE'])
    df_cf = df_cf.sort_values('REPORT_DATE')
    df_cf['FCF'] = df_cf['NETCASH_OPERATE'] - df_cf['CONSTRUCT_LONG_ASSET']
    x_hist = df_cf['REPORT_DATE'].dt.year + (df_cf['REPORT_DATE'].dt.month - 1)/12
    fcf_hist = df_cf['FCF'].values

    # --- 3. 分段增长预测 (高增长 5 年，稳定增长 3 年) ---
    last_fcf = fcf_hist[-1]
    phases = [
        {'years': 5, 'g': 0.12},
        {'years': 3, 'g': 0.06},
    ]
    fcf_forecast = []
    current = last_fcf
    for phase in phases:
        for _ in range(phase['years']):
            current *= (1 + phase['g'])
            fcf_forecast.append(current)

    # --- 4. 可视化历史 vs 预测 FCF ---
    start = x_hist.iloc[-1]
    x_pred = np.arange(start + 1/12, start + 1/12 + len(fcf_forecast))
    plt.figure(figsize=(8, 4))
    plt.plot(x_hist, fcf_hist, 'o-', label='历史 FCF')
    plt.plot(x_pred, fcf_forecast, 's--', label='预测 FCF')
    plt.title(f'{stock} 分段增长预测自由现金流（全期）')
    plt.xlabel('报告日期（年）')
    plt.ylabel('FCF (元)')
    plt.legend()
    os.makedirs('photo', exist_ok=True)
    plt.savefig(f'photo/{stock}_segmented_fcf_full.png', dpi=200, bbox_inches='tight')
    plt.close()

    # --- 5. DCF 估值 ---
    def calc_dcf(fcfs, wacc, g_perp):
        pv = sum(cf / (1 + wacc) ** (i + 1) for i, cf in enumerate(fcfs))
        tv = fcfs[-1] * (1 + g_perp) / (wacc - g_perp)
        pv_terminal = tv / (1 + wacc) ** len(fcfs)
        return pv + pv_terminal

    WACC = 0.08
    g_perp = 0.03  # 永续增长率
    ev = calc_dcf(fcf_forecast, WACC, g_perp)

    # --- 6. 读取或拉取并缓存资产负债表数据 ---
    bs_path = f"data/{stock}_资产负债.csv"
    if not os.path.exists(bs_path):
        df_bs = stock_balance_sheet_by_report_em(symbol=stock).fillna(0)
        df_bs.to_csv(bs_path, encoding="utf-8", index=False)
    else:
        df_bs = pd.read_csv(bs_path, encoding="utf-8")
    df_bs['REPORT_DATE'] = pd.to_datetime(df_bs['REPORT_DATE'])
    df_bs = df_bs.sort_values('REPORT_DATE')
    latest = df_bs.iloc[-1]
    net_debt = latest['TOTAL_LIABILITIES'] - latest['MONETARYFUNDS']

    # --- 7. 市值对比（使用缓存数据） ---
    symbol_code = int(stock.replace("sz", "").replace("sh", ""))
    market_cap = float(df_spot.loc[df_spot['代码'] == symbol_code, '总市值'].iloc[0])
    equity_val = ev - net_debt
    print(f"{stock} | EV={ev:,.0f}元 | 净债务={net_debt:,.0f}元 | 股权价值={equity_val:,.0f}元 | 市值={market_cap:,.0f}元 | 比率={equity_val/market_cap:.2f}")
    print('-'*60)
