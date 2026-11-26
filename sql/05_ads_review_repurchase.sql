-- ADS layer: does the first order's review score relate to whether a customer buys again?
-- Customers are identified by customer_unique_id (customer_id changes on every order).
-- Note: customers who first bought near the end of the data have had less time to come back.
CREATE OR REPLACE TABLE ads_review_repurchase AS
WITH ranked AS (
    SELECT
        customer_unique_id,
        review_score,
        ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY purchase_ts) AS rn,
        COUNT(*)     OVER (PARTITION BY customer_unique_id)                      AS n_orders
    FROM dwd_order
    WHERE is_valid
)
SELECT
    CASE WHEN review_score IS NULL THEN 'no review'
         ELSE CAST(CAST(round(review_score) AS INTEGER) AS VARCHAR) END AS first_order_review,
    COUNT(*)                                          AS customers,
    COUNT(*) FILTER (WHERE n_orders > 1)              AS repeat_customers,
    COUNT(*) FILTER (WHERE n_orders > 1) / COUNT(*)   AS repurchase_rate
FROM ranked
WHERE rn = 1
GROUP BY 1
ORDER BY 1;
