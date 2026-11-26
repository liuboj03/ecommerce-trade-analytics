# 数据

## 真实数据（data/raw/）

1. 打开 Kaggle 页面 [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)，登录后点 **Download**。
2. 把 zip 里的 CSV 全部解压到 `data/raw/`，目录应该是：

```
data/raw/
├── olist_customers_dataset.csv
├── olist_geolocation_dataset.csv        （本项目不使用）
├── olist_order_items_dataset.csv
├── olist_order_payments_dataset.csv
├── olist_order_reviews_dataset.csv
├── olist_orders_dataset.csv
├── olist_products_dataset.csv
├── olist_sellers_dataset.csv
└── product_category_name_translation.csv
```

数据由 Olist 在 Kaggle 上以 CC BY-NC-SA 4.0 协议公开，所以本仓库不上传原始文件（`data/raw/` 已在 `.gitignore` 中）。

## 样例数据（data/sample/）

`python scripts/make_sample_data.py` 会生成一份**模拟数据**，文件名和字段与真实数据一致，只用于测试流程是否跑通（GitHub Actions 也用它）。其中的数字没有分析意义。
