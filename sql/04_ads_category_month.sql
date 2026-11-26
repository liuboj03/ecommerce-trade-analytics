-- ADS layer: monthly GMV by category and its share of the month's total.
CREATE OR REPLACE TABLE ads_category_month AS
WITH m AS (
    SELECT
        date_trunc('month', purchase_date) AS month,
        category,
        SUM(price)                         AS gmv,
        COUNT(DISTINCT order_id)           AS orders
    FROM dwd_order_item
    WHERE is_valid
      AND purchase_date BETWEEN DATE '{analysis_start}' AND DATE '{analysis_end}'
    GROUP BY 1, 2
)
SELECT
    CAST(month AS DATE) AS month,
    category,
    gmv,
    orders,
    gmv / SUM(gmv) OVER (PARTITION BY month) AS gmv_share
FROM m
ORDER BY month, gmv DESC;
