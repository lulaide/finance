import os
import pandas as pd
import numpy as np
import akshare as ak
from scipy.optimize import bisect

# ─── 函数定义 ───────────────────────────────────────────────────────────────

def project_cash_flows(proj, horizon=5):
    """
    根据项目假设计算各期自由现金流列表（FCF）。
    proj: dict 包含 rd_schedule, capex_schedule, wc_ratio, revenue_growth, margin, tax_rate
    horizon: 预测期（年数）
    """
    fcfs = []
    revenue = 100e6  # 基准：第一年收入 1 亿元
    wc_prev = revenue * proj["wc_ratio"]
    for t in range(1, horizon + 1):
        growth = proj["revenue_growth"].get(t, list(proj["revenue_growth"].values())[-1])
        revenue *= (1 + growth)
        ebitda  = revenue * proj["margin"]
        capex   = proj["capex_schedule"].get(t, list(proj["capex_schedule"].values())[-1])
        rd      = proj["rd_schedule"].get(t, list(proj["rd_schedule"].values())[-1])
        wc      = revenue * proj["wc_ratio"]
        d_wc    = wc - wc_prev
        wc_prev = wc
        # 税前利润 = EBITDA - CapEx - R&D - ΔWC
        taxable = max(ebitda - capex - rd - d_wc, 0)
        tax     = taxable * proj["tax_rate"]
        fcf     = ebitda - capex - rd - d_wc - tax
        fcfs.append(fcf)
    return fcfs

def npv(cfs, wacc, I_total):
    """
    贴现现金流净现值 (NPV)
    cfs: list of FCF (t=1 开始)
    wacc: 折现率
    I_total: 初始投资总额
    """
    return sum(cf / (1 + wacc)**i for i, cf in enumerate(cfs, start=1)) - I_total

def irr(cfs, I_total, tol=1e-6):
    """
    内部收益率 IRR，使用二分法求解。
    cfs: list of FCF (t=1 开始)
    I_total: 初始投资总额
    """
    flows = [-I_total] + cfs
    f = lambda r: sum(cf / (1 + r)**i for i, cf in enumerate(flows))
    try:
        return bisect(f, -0.9, 1.0, xtol=tol)
    except ValueError:
        return float("nan")

def payback_period(cfs, I_total):
    """
    投资回收期（Payback Period）
    cfs: list of FCF (t=1 开始)
    I_total: 初始投资总额
    """
    cum = 0
    for i, cf in enumerate(cfs, start=1):
        cum += cf
        if cum >= I_total:
            return i
    return None

# ─── 主程序 ────────────────────────────────────────────────────────────────

symbols = [
    "sz000598","sz000605","sz000685","sz003039",
    "sh600008","sh600168","sh600187","sh600283",
    "sh600461","sh600769","sh601158","sh601199",
    "sh601368","sh603291","sh603759",
]

os.makedirs("data", exist_ok=True)
results = []

for stock in symbols:
    # 1. 缓存并加载财务报表
    p_path = f"data/{stock}_利润表.csv"
    if not os.path.exists(p_path):
        df_p = ak.stock_profit_sheet_by_report_em(symbol=stock).fillna(0)
        df_p.to_csv(p_path, index=False, encoding="utf-8")
    else:
        df_p = pd.read_csv(p_path, encoding="utf-8")

    c_path = f"data/{stock}_现金流.csv"
    if not os.path.exists(c_path):
        df_c = ak.stock_cash_flow_sheet_by_report_em(symbol=stock).fillna(0)
        df_c.to_csv(c_path, index=False, encoding="utf-8")
    else:
        df_c = pd.read_csv(c_path, encoding="utf-8")

    b_path = f"data/{stock}_资产负债.csv"
    if not os.path.exists(b_path):
        df_b = ak.stock_balance_sheet_by_report_em(symbol=stock).fillna(0)
        df_b.to_csv(b_path, index=False, encoding="utf-8")
    else:
        df_b = pd.read_csv(b_path, encoding="utf-8")

    # 2. 提取最新一期关键比率
    df_p["REPORT_DATE"] = pd.to_datetime(df_p["REPORT_DATE"])
    last_p = df_p.sort_values("REPORT_DATE").iloc[-1]
    df_c["REPORT_DATE"] = pd.to_datetime(df_c["REPORT_DATE"])
    last_c = df_c.sort_values("REPORT_DATE").iloc[-1]
    df_b["REPORT_DATE"] = pd.to_datetime(df_b["REPORT_DATE"])
    last_b = df_b.sort_values("REPORT_DATE").iloc[-1]

    rev   = last_p["TOTAL_OPERATE_INCOME"]
    rd    = last_p.get("RESEARCH_EXPENSE", 0)
    capex = last_c.get("CONSTRUCT_LONG_ASSET", 0)
    ca = last_b["MONETARYFUNDS"] + last_b.get("INVENTORY", 0) + last_b.get("ACCOUNTS_RECE", 0)
    cl = last_b.get("ACCOUNTS_PAYABLE", 0) + last_b.get("ADVANCE_RECEIVABLES", 0)

    rd_intensity    = rd / rev   if rev else 0
    capex_intensity = capex / rev if rev else 0
    wc_ratio        = (ca - cl) / rev if rev else 0

    # 3. 构造项目假设
    project_i = {
        "rd_schedule":    {1: rd_intensity * 100e6, 2: rd_intensity * 120e6, 3: rd_intensity * 80e6},
        "capex_schedule": {1: capex_intensity * 100e6, 2: capex_intensity * 80e6, 3: capex_intensity * 60e6},
        "wc_ratio":       wc_ratio,
        "revenue_growth": {1: 0.10, 2: 0.12, 3: 0.08, 4: 0.06, 5: 0.04},
        "margin":         0.30,
        "tax_rate":       0.25
    }
    horizon = 5
    WACC    = 0.10
    I_total = sum(project_i["rd_schedule"].values()) + sum(project_i["capex_schedule"].values())

    # 4. 计算现金流与指标
    fcfs        = project_cash_flows(project_i, horizon)
    npv_i       = npv(fcfs, WACC, I_total)
    irr_i       = irr(fcfs, I_total)
    payback_i   = payback_period(fcfs, I_total)
    roi_i       = sum(fcfs) / I_total if I_total else float("nan")

    results.append({
        "stock":   stock,
        "NPV":     npv_i,
        "IRR":     irr_i,
        "Payback": payback_i,
        "ROI":     roi_i
    })

# 5. 保存并输出结果
df_out = pd.DataFrame(results)
print(df_out)
