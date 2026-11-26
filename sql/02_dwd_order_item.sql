-- DWD layer: one row per order item, with the English category name.
CREATE OR REPLACE TABLE dwd_order_item AS
SELECT
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    oi.seller_id,
    oi.price,
    oi.freight_value,
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
    d.purchase_date,
    d.customer_unique_id,
    d.is_valid
FROM order_items oi
JOIN dwd_order d                    USING (order_id)
LEFT JOIN products p                USING (product_id)
LEFT JOIN category_translation t    USING (product_category_name);
