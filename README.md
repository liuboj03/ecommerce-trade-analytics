# 电商交易数据监控与大促复盘

![pipeline-test](../../actions/workflows/ci.yml/badge.svg)

这个项目基于巴西电商平台 Olist 公开的约 10 万笔订单数据（2016–2018），模拟交易分析岗位的日常工作：**用 SQL 搭建交易指标体系 → 每日自动监控和异常预警 → 黑色星期五大促复盘 → 沉淀指标口径与数据字典**。整个流程可以一键复现。

## 要回答的业务问题

1. **日常监控：** 每天的 GMV、订单量、客单价、差评率是否正常？哪天出现了异常，异常是上升还是下降？
2. **活动复盘：** 2017 年黑色星期五当周，GMV 比平时高了多少？增长来自更多的买家、更高的购买频次，还是更高的客单价？哪些品类贡献了主要增量？
3. **交易结构：** GMV 主要集中在哪些品类？结构如何随时间变化？
4. **体验与复购：** 首单评价的好坏，和用户是否再次购买有没有关系？

## 结果

> 用真实数据运行后，把 `reports/summary.md` 中的关键结论整理到这里，每条写成"发现 + 数字 + 建议"。

![每日 GMV 与自动预警](reports/figures/daily_gmv_alerts.png)
![大促 GMV 拆解](reports/figures/campaign_decomposition.png)
![品类 GMV 占比](reports/figures/category_share.png)
![首单评分与复购率](reports/figures/review_repurchase.png)

交互看板：Tableau Public 链接（用 `reports/tables/` 中导出的 CSV 搭建，搭好后贴在这里）

## 方法

| 模块 | 做法 | 代码 |
|---|---|---|
| 数据建模 | 原始表 → DWD 明细层（一单一行、一件商品一行）→ ADS 应用层（日指标、品类月度、评价复购），全部用 SQL 在 DuckDB 中完成 | `sql/` |
| 指标体系 | GMV、订单量、下单用户数、客单价、取消率、差评率、延迟送达率，口径统一写在文档中 | `docs/metric_definitions.md` |
| 异常预警 | 每个指标与前 28 天（不含当天）比较，\|z\| > 3 触发预警，并自动生成日报：环比、周同比、对比 28 天均值 | `src/monitor.py` |
| 活动复盘 | GMV = 下单用户数 × 人均订单数 × 客单价，用对数拆解计算每个因素对 GMV 变化的贡献；再按品类计算增量 GMV | `src/campaign.py` |
| 可视化 | Python 生成静态图；导出 CSV 给 Tableau 做交互看板 | `src/charts.py` |
| 可复现 | 一条命令跑完全流程；GitHub Actions 每次提交都会用模拟数据自动测试 | `src/run_pipeline.py`、`tests/` |

## 快速开始

```bash
git clone <本仓库地址>
cd ecommerce-trade-analytics
pip install -r requirements.txt

# 1. 下载真实数据，放到 data/raw/（步骤见 data/README.md）
# 2. 运行全流程
python -m src.run_pipeline --data raw
```

运行后会生成：

```
reports/
├── summary.md                      关键结论（自动生成）
├── daily_report_2017-11-24.md      黑五当天的监控日报
├── daily_report_2018-08-31.md      窗口最后一天的监控日报
├── figures/                        4 张图
└── tables/                         导出给 Tableau 的 CSV（日指标、预警清单、复盘结果等）
```

没有下载数据也可以先体验：`python scripts/make_sample_data.py && python -m src.run_pipeline --data sample`。这会生成一份字段相同的**模拟数据**，只用来检查流程，数字没有分析意义。

## 项目结构

```
├── sql/                    SQL 数据分层：DWD 明细层与 ADS 应用层
├── src/
│   ├── config.py           路径、分析窗口、预警阈值、活动日期
│   ├── load.py             读入 CSV，按顺序执行 sql/
│   ├── monitor.py          异常检测与监控日报
│   ├── campaign.py         大促复盘与 GMV 拆解
│   ├── charts.py           图表
│   └── run_pipeline.py     一键运行入口
├── docs/                   指标口径、数据字典
├── scripts/                模拟数据生成
├── tests/                  端到端测试
└── data/                   数据说明（原始数据不上传）
```

## 局限与可以继续做的

- 预警规则是 3σ，没有单独处理周内效应和节假日，大促一定会触发预警。下一步可以按星期几分别建基线，或用 STL 分解去掉季节性后再判断。
- 复盘对比的是活动周和活动前 4 周，没有对照组，所以结论是"相关"而不是严格的因果。可以按地区或品类构造对照组做双重差分。
- 复购分析中，越晚首购的用户可观察时间越短，后续可以只看首购后满 90 天的用户。

## 数据来源

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)（Kaggle，CC BY-NC-SA 4.0）
