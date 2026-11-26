-- ADS layer: does late delivery hurt the review score?
-- Only delivered orders that have a review are compared.
CREATE OR REPLACE TABLE ads_delivery_review AS
SELECT
    CASE WHEN is_late THEN 'late' ELSE 'on time' END            AS delivery,
    COUNT(*)                                                     AS orders,
    AVG(review_score)                                            AS avg_review_score,
    COUNT(*) FILTER (WHERE review_score <= 2) / COUNT(*)         AS bad_review_rate
FROM dwd_order
WHERE is_late IS NOT NULL
  AND review_score IS NOT NULL
  AND purchase_date BETWEEN DATE '{analysis_start}' AND DATE '{analysis_end}'
GROUP BY 1
ORDER BY 1 DESC;
