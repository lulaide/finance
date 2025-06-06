# 重庆邮电大学数学建模竞赛题目B
> [!NOTE]
[**@lulaide**](https://github.com/lulaide)  
[**@BailPlus**](https://github.com/BailPlus)
## 环境准备
```bash
pip install -r requirements.txt
```
```bash
pip install -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
```
## 问题一
### 1.问题描述
根据给出的参考数据（来源于上市公司公布的财务数据），构建一个全面而灵活的财务评价优化模型，以支持研发企业在投资或收购决策过程中做出科学和合理的选择。该模型应包括设计项目总投资公式，全面考虑研发、财务、债务、运营等因素（也可根据模型自主选取），并设计收益率指标公式，计算主要指标波动等影响因素。之后对财务效益进行多因素敏感性模拟分析，以量化各个因素对项目财务效益的影响程度，从中识别出对项目收益影响最大的关键因素和潜在风险。最后，根据敏感性分析结果，提出优化策略，如调整研发投入的阶段性、优化资源配置和制定灵活市场响应机制，以最大化项目的预期收益并有效控制相关风险。

---
## 问题二
### 1.问题描述
请构建一个多维度的**企业价值评估模型**，使得不同企业的信息输入后，生成相应的**综合价值评分**。通过该评估模型，投资者可以对各个企业进行**评分和排序**，从而为投资决策提供有力支持。
### 2.估值方法
#### 折现现金流量法(DCF Analysis)
这里代码中 FCF 的预估方法为：

FCF = NETCASH_OPERATE - CONSTRUCT_LONG_ASSET

DCF 的核心估值公式为：

Valuation = Σ(FCF_t / (1 + r)^t) + (FCF_n * (1 + g_infinity)) / ((r - g_infinity) * (1 + r)^n)

其中，r 为加权平均资本成本（WACC），$g_{\infty}$ 为永续增长率。

以下是相应的代码示例（摘自 DCF.py）：
```python
def calc_dcf(fcfs, wacc, g_perp):
    # 对预测期内各期 FCF 进行贴现求和
    pv = sum(cf / (1 + wacc) ** (i + 1) for i, cf in enumerate(fcfs))
    # 计算终值 (Terminal Value)
    tv = fcfs[-1] * (1 + g_perp) / (wacc - g_perp)
    pv_terminal = tv / (1 + wacc) ** len(fcfs)
    return pv + pv_terminal
```
以下是示例输出（摘自 DCF.py）：
```
sz000598 | EV=-38,322,284,987元 | 净债务=24,554,330,613元 | 股权价值=-62,876,615,601元 | 市值=21,428,241,297元 | 比率=-2.93
------------------------------------------------------------
sz000605 | EV=-1,127,073,243元 | 净债务=4,829,130,451元 | 股权价值=-5,956,203,694元 | 市值=2,673,152,188元 | 比率=-2.23
------------------------------------------------------------
sz000685 | EV=-17,787,771,376元 | 净债务=15,591,827,097元 | 股权价值=-33,379,598,473元 | 市值=12,730,210,959元 | 比率=-2.62
------------------------------------------------------------
sz003039 | EV=-2,805,139,606元 | 净债务=2,972,818,215元 | 股权价值=-5,777,957,821元 | 市值=8,669,962,969元 | 比率=-0.67
------------------------------------------------------------
sh600008 | EV=-24,774,431,800元 | 净债务=66,553,670,125元 | 股权价值=-91,328,101,925元 | 市值=23,049,454,726元 | 比率=-3.96
------------------------------------------------------------
sh600168 | EV=-17,225,596,757元 | 净债务=17,172,522,238元 | 股权价值=-34,398,118,995元 | 市值=4,619,298,696元 | 比率=-7.45
------------------------------------------------------------
sh600187 | EV=-1,717,496,735元 | 净债务=-42,743,490元 | 股权价值=-1,674,753,245元 | 市值=5,147,961,719元 | 比率=-0.33
------------------------------------------------------------
sh600283 | EV=-3,709,664,370元 | 净债务=4,746,019,644元 | 股权价值=-8,455,684,014元 | 市值=5,978,393,413元 | 比率=-1.41
------------------------------------------------------------
sh600461 | EV=-6,167,809,826元 | 净债务=11,416,024,021元 | 股权价值=-17,583,833,847元 | 市值=12,379,254,113元 | 比率=-1.42
------------------------------------------------------------
sh600769 | EV=410,690,891元 | 净债务=109,198,728元 | 股权价值=301,492,163元 | 市值=4,061,003,076元 | 比率=0.07
------------------------------------------------------------
sh601158 | EV=-8,422,250,548元 | 净债务=17,035,285,191元 | 股权价值=-25,457,535,739元 | 市值=23,616,000,000元 | 比率=-1.08
------------------------------------------------------------
sh601199 | EV=-1,522,201,446元 | 净债务=1,573,245,734元 | 股权价值=-3,095,447,180元 | 市值=5,078,191,886元 | 比率=-0.61
------------------------------------------------------------
sh601368 | EV=-22,830,438,751元 | 净债务=18,016,650,942元 | 股权价值=-40,847,089,692元 | 市值=4,600,289,731元 | 比率=-8.88
------------------------------------------------------------
sh603291 | EV=-1,634,723,152元 | 净债务=1,775,682,786元 | 股权价值=-3,410,405,937元 | 市值=5,379,133,877元 | 比率=-0.63
------------------------------------------------------------
sh603759 | EV=-1,200,483,402元 | 净债务=3,619,316,137元 | 股权价值=-4,819,799,539元 | 市值=3,721,785,600元 | 比率=-1.30
```
#### 席勒市盈率法(CAPE)
在 `CAPE.py` 中，流程如下：

1. 从利润表中提取 `BASIC_EPS`，按年度分组并计算近 10 年的 EPS 均值：

    EPS_10y = (1 / 10) * Σ(EPS_i) for i in range(1, 11)

2. 获取股票最新的收盘价：

    Close = latest closing price

3. 计算席勒市盈率（CAPE）：

    CAPE = Close / EPS_10y
以下是核心代码示例：
```python
# 转换 REPORT_DATE 为 datetime, 排序, 并提取年度 EPS 均值
df_inc["REPORT_DATE"] = pd.to_datetime(df_inc["REPORT_DATE"])
df_inc = df_inc.sort_values("REPORT_DATE")
df_inc["year"] = df_inc["REPORT_DATE"].dt.year
eps_yearly = df_inc.groupby("year")["BASIC_EPS"].mean()
eps_10y = eps_yearly.tail(10)
avg_eps_10y = eps_10y.mean()

# 获取每日历史行情的最新收盘价
df_price = pd.read_csv(daily_path, encoding="utf-8", parse_dates=["date"])
latest_close = df_price.sort_values("date").iloc[-1]["close"]

# 计算 CAPE
cape = latest_close / avg_eps_10y if avg_eps_10y != 0 else float("nan")
```
以下是示例输出（摘自 CAPE.py）：
```bash
       stock  最新收盘价   十年平均EPS  席勒市盈率(CAPE)
0   sz000685   8.82  0.440750    20.011344
1   sh600168   4.63  0.211250    21.917160
2   sh600461   9.59  0.431750    22.211928
3   sh600008   3.18  0.135680    23.437500
4   sh601158   4.92  0.199500    24.661654
5   sz000598   7.21  0.276040    26.119403
6   sh601368   4.92  0.165615    29.707454
7   sh601199   5.38  0.172035    31.272706
8   sh603759   8.02  0.244908    32.747058
9   sz003039  13.82  0.234194    59.010863
10  sh600283  10.74  0.175500    61.196581
11  sh603291  12.73  0.154144    82.585182
12  sz000605   7.58  0.076332    99.302394
13  sh600769  10.67  0.012500   853.600000
14  sh600187   3.20  0.001070  2990.654206
```

---
## 问题三
### 1.问题描述
针对不同类型的投资项目（如新建、扩建、改建等），构建一个动态风险评估模型，以量化各类风险（如市场风险、技术风险、政策风险等），识别项目面临的各种风险因素，并评估整体风险水平及各因素的影响程度，从而为项目风险管理提供有力支持。

### 2. 市场风险
量化方法：VaR (Value at Risk)

#### 理论基础
在险价值（Value at Risk, VaR）是指特定时间长度内在一定信赖程度上的最大可能损失情形。1993年由G30集团在《衍生产品的实践和规则》报告中提出，用以克服资产负债管理方法过于依赖报表（报表更新过慢，时效性差，无法满足金融业信息更新需求），β和方差方法只能给出波动幅度且过于抽象，以及CAPM方法无法糅合各类金融衍生品的特点。

VaR方法能够给出一定条件下损失最大值的情况，较为直观地反应了风险。虽然VaR方法如今饱受争议，但是其简单、直观的且能不断改进的特性，使其仍然保留不可动摇，难以替代的地位，在金融风险管理方面发挥巨大作用。


由于数据提供的局限性等原因，决定采用历史模拟法计算VaR。

#### 模型构建
- 模型输入：项目信息、财务数据、历史数据、市场数据、模型参数
- 模型输出：项目风险等级、项目风险因素
- 计算方法：
1. 收集历史数据
收集一定历史期间的资产价格数据（如股票、债券、商品等）。数据应包括：
历史价格（通常是每日收盘价）；
或者收益率数据（如每天的收益率，通常为对数收益）。

2. 计算每日收益率
基于收集到的历史数据，计算每一天的 收益率。计算公式为：
$$
R_t = \frac{P_t - P_{t-1}}{P_{t-1}} \quad \text{或} \quad R_t = \ln\left(\frac{P_t}{P_{t-1}}\right)
$$

3. 排序收益率
将计算得到的每日收益率从高到低排列。这一步是为了便于在后续计算VaR时找出特定置信度水平对应的损失水平。

4. 确定VaR的置信水平
选择一个置信水平，通常为 95%，意味着关注的是收益率分布中最坏的 5%（即位于下5%的部分）。

5. 计算VaR
如果有$N$天的历史收益数据，按照步骤3排序后，找出排名在前5%（或置信度所对应的百分位数）的收益率值。对于95%的置信度，VaR 就是第$5N$排名的收益率。

6. 转换到货币损失
最后可以根据投资组合的总价值，将其转化为货币损失：
$$
\text{VaR}_{\text{货币}} = \text{VaR}_{\text{收益率}} \times \text{投资组合价值}
$$
#### 优缺点：
优点：无需假设数据分布类型，计算简单直接，适合各种资产。
缺点：完全依赖历史数据，不能有效捕捉未来极端事件（比如“黑天鹅”事件），无法反映在极端市场条件下的风险。

#### 代码实现
```python
symbol = '<股票代码>'
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

return float(var_pct)
```

#### 其他模型
除了价格—均线偏离这种“技术指标”风险，典型的市场风险还包括以下几类：

1. 利率风险 (Interest­-Rate Risk)
定义：因市场利率变动导致资产或负债公允价值波动的风险。
量化方法：
DV01（对久期的敏感度）：
$$
\text{DV01} = -\frac{\Delta P}{\Delta y}\times 0.0001
$$

2. 汇率风险 (Foreign­-Exchange Risk)
定义：因货币汇率波动导致跨境敞口（收入、成本或头寸）价值变化的风险。

3. 商品风险 (Commodity Risk)
定义：大宗商品（能源、金属、农产品）价格波动带来的风险。
量化方法：
商品价格 VaR 或 CVaR。
使用期货曲线（contango/backwardation）进行情景模拟。
4. 波动率风险 (Volatility Risk)
定义：隐含或历史波动率剧烈变动对期权或波动率衍生品头寸价值的影响。
量化方法：
Vega 敏感度：
$$
\text{Vega} = \frac{\partial V}{\partial \sigma}
$$

5. 信用利差风险 (Credit­-Spread Risk)
定义：债券或信用衍生品的信用利差 (spread) 变动导致估值损益。
量化方法：
Spread duration：
$$
\text{SpreadDuration} = -\frac{\Delta P}{\Delta s}
$$

6. 流动性风险 (Liquidity Risk)
定义：市场深度不足或成交不活跃导致大额头寸难以清算或清算成本大幅上升的风险。
量化方法：
Bid–Ask spread 分析。
Market‑impact 模型：。
持仓可变现日数 (Days‑to‑Liquidate, DTL)。

7. 基差风险 (Basis Risk)
定义：现货与衍生品（如期货、互换）之间的价差（基差）变动风险。
量化方法：
历史基差波动率。
基差 VaR。

8. 相关性/集中度风险 (Correlation / Concentration Risk)
定义：资产间相关性突变导致分散效果失效，或单一敞口过度集中。
量化方法：
协方差矩阵压力测试（stress‑test）。
分散度指标（Herfindahl–Hirschman Index）。

9. 尾部风险 (Tail Risk)
定义：极端市场事件（如黑天鹅）引发的巨幅损失风险。
量化方法：
极值理论 (EVT)：峰值过阈建模估计极端回撤概率。
CVaR (Conditional VaR) 衡量极端损失的平均值。

10. 系统性风险 (Systemic Risk)
定义：整个金融系统或市场链条传染放大，导致系统性崩溃的风险。
量化方法：
CoVaR（Conditional VaR）：衡量在一家机构违约时，对其他机构的溢出损失。
网络模型：金融机构间暴露网络的模拟。

### 3. 技术风险
量化方法：现价相较于MA20的涨幅

#### 代码实现
```python
symbol = '<股票代码>'
df = ak.stock_zh_a_daily(symbol)
# 计算MA20
df['MA20'] = df['close'].rolling(window=20).mean()
# 计算现价相较于MA20的涨幅
df['technical_risk'] = (df['close'] - df['MA20']) / df['MA20']
# 统计均值
technical_risk = sum([df['technical_risk'].iloc[i] for i in range(19,len(df) - 1)])/len(df)
return technical_risk
```

### 4. 政策风险

---

## 参考资料
- [什么是估值？其运作方式及方法](https://www.investopedia.com/terms/v/valuation.asp)
- [估值概述](https://corporatefinanceinstitute.com/resources/valuation/valuation/)
- [现金流 DCF 公式](https://corporatefinanceinstitute.com/resources/valuation/dcf-formula-guide/)
- [金融学习笔记（十二）：VaR(Value at Risk)](https://zhuanlan.zhihu.com/p/412026199)
- [Python量化金融风险分析：一文全面掌握VaR计算](https://blog.csdn.net/aobulaien001/article/details/132911177)
