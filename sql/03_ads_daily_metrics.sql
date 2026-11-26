-- ADS layer: daily trade monitoring table. A calendar spine makes days with
-- zero orders show up as 0 instead of disappearing (otherwise an outage is invisible).
CREATE OR REPLACE TABLE ads_daily_metrics AS
WITH calendar AS (
    SELECT CAST(d AS DATE) AS dt
    FROM range(DATE '{analysis_start}', DATE '{analysis_end}' + INTERVAL 1 DAY, INTERVAL 1 DAY) t(d)
),
daily AS (
    SELECT
        purchase_date                                             AS dt,
        COUNT(*)                                                  AS orders_all,
        COUNT(*) FILTER (WHERE is_valid)                          AS orders,
        COUNT(DISTINCT customer_unique_id) FILTER (WHERE is_valid) AS buyers,
        SUM(item_amount) FILTER (WHERE is_valid)                  AS gmv,
        COUNT(*) FILTER (WHERE order_status = 'canceled')         AS canceled_orders,
        COUNT(review_score)                                       AS reviewed_orders,
        COUNT(*) FILTER (WHERE review_score <= 2)                 AS bad_review_orders,
        COUNT(is_late)                                            AS delivered_orders,
        COUNT(*) FILTER (WHERE is_late)                           AS late_orders
    FROM dwd_order
    GROUP BY purchase_date
)
SELECT
    c.dt,
    dayname(c.dt)                                   AS weekday,
    COALESCE(d.orders_all, 0)                       AS orders_all,
    COALESCE(d.orders, 0)                           AS orders,
    COALESCE(d.buyers, 0)                           AS buyers,
    COALESCE(d.gmv, 0)                              AS gmv,
    d.gmv / NULLIF(d.orders, 0)                     AS aov,
    d.canceled_orders / NULLIF(d.orders_all, 0)     AS cancel_rate,
    d.bad_review_orders / NULLIF(d.reviewed_orders, 0) AS bad_review_rate,
    d.late_orders / NULLIF(d.delivered_orders, 0)   AS late_rate
FROM calendar c
LEFT JOIN daily d USING (dt)
ORDER BY c.dt;
