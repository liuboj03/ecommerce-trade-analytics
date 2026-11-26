-- DWD layer: one row per order, joining items, payments, reviews and customers.
-- GMV in this project = sum of item price for valid orders (freight excluded).
CREATE OR REPLACE TABLE dwd_order AS
WITH items AS (
    SELECT order_id,
           COUNT(*)           AS item_cnt,
           SUM(price)         AS item_amount,
           SUM(freight_value) AS freight_amount
    FROM order_items
    GROUP BY order_id
),
pay AS (
    SELECT order_id,
           SUM(payment_value)                    AS pay_amount,
           arg_max(payment_type, payment_value)  AS main_payment_type,
           MAX(payment_installments)             AS max_installments
    FROM order_payments
    GROUP BY order_id
),
rev AS (
    -- a few orders have more than one review: keep the average score
    SELECT order_id, AVG(review_score) AS review_score
    FROM order_reviews
    GROUP BY order_id
)
SELECT
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_state,
    o.order_status,
    CAST(o.order_purchase_timestamp AS TIMESTAMP)       AS purchase_ts,
    CAST(o.order_purchase_timestamp AS DATE)            AS purchase_date,
    CAST(o.order_delivered_customer_date AS TIMESTAMP)  AS delivered_ts,
    CAST(o.order_estimated_delivery_date AS TIMESTAMP)  AS estimated_ts,
    COALESCE(i.item_cnt, 0)        AS item_cnt,
    COALESCE(i.item_amount, 0)     AS item_amount,
    COALESCE(i.freight_amount, 0)  AS freight_amount,
    p.pay_amount,
    p.main_payment_type,
    p.max_installments,
    r.review_score,
    o.order_status NOT IN ('canceled', 'unavailable') AS is_valid,
    CASE WHEN o.order_delivered_customer_date IS NOT NULL
         THEN CAST(o.order_delivered_customer_date AS TIMESTAMP)
              > CAST(o.order_estimated_delivery_date AS TIMESTAMP)
    END AS is_late
FROM orders o
LEFT JOIN customers c USING (customer_id)
LEFT JOIN items i     USING (order_id)
LEFT JOIN pay p       USING (order_id)
LEFT JOIN rev r       USING (order_id);
