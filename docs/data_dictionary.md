# 数据字典（Data dictionary）

## 数据分层

```
data/raw/*.csv  ──►  原始表（orders, order_items, ...）
                       │  sql/01, 02
                       ▼
                     DWD 明细层：dwd_order（一单一行）、dwd_order_item（一件商品一行）
                       │  sql/03, 04, 05
                       ▼
                     ADS 应用层：ads_daily_metrics、ads_category_month、ads_review_repurchase
                       │  src/*.py
                       ▼
                     reports/：监控日报、预警清单、活动复盘、图表、导出给 Tableau 的 CSV
```

## 原始表

| 表 | 来源文件 | 粒度 | 主要字段 |
|---|---|---|---|
| orders | olist_orders_dataset.csv | 一笔订单 | order_id, customer_id, order_status, order_purchase_timestamp, order_delivered_customer_date, order_estimated_delivery_date |
| order_items | olist_order_items_dataset.csv | 一件商品 | order_id, order_item_id, product_id, seller_id, price, freight_value |
| order_payments | olist_order_payments_dataset.csv | 一次支付 | order_id, payment_type, payment_installments, payment_value |
| order_reviews | olist_order_reviews_dataset.csv | 一条评价 | review_id, order_id, review_score, review_comment_message |
| customers | olist_customers_dataset.csv | 一个订单下的客户 | customer_id, customer_unique_id, customer_state |
| products | olist_products_dataset.csv | 一个商品 | product_id, product_category_name |
| sellers | olist_sellers_dataset.csv | 一个卖家 | seller_id, seller_state |
| category_translation | product_category_name_translation.csv | 一个品类 | product_category_name, product_category_name_english |

## DWD 明细层

**dwd_order**（一单一行）

| 字段 | 含义 |
|---|---|
| order_id / customer_unique_id / customer_state | 订单、用户、用户所在州 |
| order_status / is_valid | 订单状态；是否为有效订单 |
| purchase_ts / purchase_date | 下单时间、下单日期 |
| item_cnt / item_amount / freight_amount | 商品件数、商品金额（GMV 口径）、运费 |
| pay_amount / main_payment_type / max_installments | 实付金额、主要支付方式、最大分期数 |
| review_score | 评分（多条评价取平均） |
| is_late | 是否晚于预计送达（未送达为空） |

**dwd_order_item**（一件商品一行）：order_id、product_id、seller_id、price、freight_value、category（英文品类名）、purchase_date、customer_unique_id、is_valid。

## ADS 应用层

| 表 | 粒度 | 用途 |
|---|---|---|
| ads_daily_metrics | 一天 | 日度监控：GMV、订单、用户、客单价、取消率、差评率、延迟率 |
| ads_category_month | 月 × 品类 | 品类结构与占比变化 |
| ads_review_repurchase | 首单评分 | 评价与复购的关系 |

各指标的计算口径见 [metric_definitions.md](metric_definitions.md)。
