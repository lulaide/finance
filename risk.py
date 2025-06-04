from matplotlib import pyplot as plt
import os
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

def calculate_var(df:pd.DataFrame,
                  confidence_level: float = 0.95) -> pd.Series:
    """
    计算单只股票基于非重叠周度对数收益的历史模拟 VaR（百分比形式，正数表示损失）
    Params:
      symbol: AkShare 支持的 A 股代码，如 "sz000001"
      confidence_level: 置信水平，默认 0.95
    Returns:
      VaR 值（正数），表示该水平下一周最大可能损失比例
    """
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

def calculate_technical(df: pd.DataFrame)->pd.Series:
    """计算技术风险
symbols(str):股票代码
返回值:技术风险(pd.Series)
-----
通过相对涨幅进行量化"""
    # 计算MA20
    min_periods = 20
    df['MA20'] = df['close'].rolling(window=min_periods).mean()
    # 计算现价相较于MA20的涨幅
    df['technical_risk'] = (df['close'] - df['MA20']) / df['MA20']
    # 统计均值
    technical_risk = sum(
        [df['technical_risk'].iloc[i] for i in range(19, len(df) - 1)]
    ) / len(range(19, len(df) - 1))
    technical_risk_series = df['technical_risk'].expanding(min_periods=min_periods).mean()
    return technical_risk_series

def draw(name:str,stock:str,series: pd.Series):
    """画图
name(str):图表名称
stock(str):股票代码
series(pd.Series):数据"""
    plt.title(f'Trend of {stock}_{name}')
    plt.xlabel('Time')
    plt.ylabel('Value')
    for i in series.index:
        plt.scatter(i,series.loc[i],marker='o',s=1)
    plt.savefig(f'photo/{stock}_{name}.png')
    plt.close()

def init():
    os.makedirs('photo', exist_ok=True)

def get_dataframe(symbol:str)->pd.DataFrame:
    # 获取日线行情
    df = ak.stock_zh_a_daily(symbol)
    # 转成 DatetimeIndex
    df['date'] = pd.to_datetime(df['date'])
    return df.set_index('date').sort_index()

if __name__ == "__main__":
    init()
    for sym in symbols:
        df = get_dataframe(sym)
        var = calculate_var(df)
        tech = calculate_technical(df)
        print(f"{sym} 一周市场风险 = {var.iloc[-1] * 100:.2f}%")
        print(f"{sym} 技术风险 = {tech.iloc[-1] * 100:.2f}%")
        ##draw('VaR',sym,var)
        draw('technical risk',sym,tech)
