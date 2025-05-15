from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import akshare as ak

# 要计算的一组个股列表
symbols = [
    "sz000598", "sz000605", "sz000685", "sz003039",
    "sh600008", "sh600168", "sh600187", "sh600283",
    "sh600461", "sh600769", "sh601158", "sh601199",
    "sh601368", "sh603291", "sh603759",
]

def calculate_var(symbol: str,
                  confidence_level: float = 0.95) -> pd.Series:
    """
    计算单只股票基于非重叠周度对数收益的历史模拟 VaR（百分比形式，正数表示损失）
    Params:
      symbol: AkShare 支持的 A 股代码，如 "sz000001"
      confidence_level: 置信水平，默认 0.95
    Returns:
      VaR 值（正数），表示该水平下一周最大可能损失比例
    """
    # 获取日线行情
    df = ak.stock_zh_a_daily(symbol)
    # 转成 DatetimeIndex
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()

    # 计算对数收益
    df['log_ret'] = np.log(df['close']) - np.log(df['close'].shift(1))
    df = df.dropna(subset=['log_ret'])

    # 按周五非重叠累加对数收益
    # 'W-FRI'：星期五为周的结束点
    weekly_ret = df['log_ret'].resample('W-FRI').sum().dropna()

    # 计算 5% 分位数（即 1 - confidence_level）
    # 取负号将其转为正的损失值
    var_pct = -np.percentile(weekly_ret, (1 - confidence_level) * 100)
    var_series = weekly_ret.expanding(min_periods=1).apply(
        lambda x: -np.percentile(x, (1 - confidence_level) * 100),
        raw=True
    )
    return var_series

def calculate_technical(symbol: str)->pd.Series:
    df = ak.stock_zh_a_daily(symbol)
    # 计算MA20
    min_periods = 20
    df['MA20'] = df['close'].rolling(window=min_periods).mean()
    # 计算现价相较于MA20的涨幅
    df['technical_risk'] = (df['close'] - df['MA20']) / df['MA20']
    # 统计均值
    technical_risk_series = df['technical_risk'].expanding(min_periods=min_periods).mean()
    technical_risk = sum([df['technical_risk'].iloc[i] for i in range(19,len(df) - 1)])/len(df)
    return technical_risk_series

def draw_var(symbol: str):
    pass
    
if __name__ == "__main__":
    for sym in symbols:
        var = calculate_var(sym).iloc[-1]
        tech = calculate_technical(sym).iloc[-1]
        print(f"{sym} 一周市场风险 = {var * 100:.2f}%")
        print(f"{sym} 技术风险 = {tech * 100:.2f}%")
