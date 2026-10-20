-- Step 2 · Question 1: Where does the spend sit?
-- Builds one row per supplier with its spend, activity and A / B / C segment.
-- Segment rule: rank suppliers by 3-year spend; A = suppliers making up the first 70% of spend,
-- B = the next 22% (up to 92%), C = the long tail.
-- Inactive = no purchase order in the last 18 months of the data (data ends 2015-06-30).

DROP TABLE IF EXISTS supplier_segments;

CREATE TABLE supplier_segments AS
WITH s AS (
  SELECT supplier_code,
         MAX(supplier_name)                                   AS supplier_name,
         SUM(amount_usd)                                      AS spend_usd,
         COUNT(*)                                             AS po_lines,
         COUNT(DISTINCT purchase_order_number)                AS po_count,
         COUNT(DISTINCT department_name)                      AS departments,
         COUNT(DISTINCT family_title)                         AS categories,
         MAX(creation_date)                                   AS last_po_date,
         MAX(CASE WHEN supplier_qualifications LIKE '%SB%'
                    OR supplier_qualifications LIKE '%DVBE%' THEN 1 ELSE 0 END) AS small_or_diverse
  FROM spend_lines
  GROUP BY supplier_code
), ranked AS (
  SELECT s.*,
         ROW_NUMBER() OVER (ORDER BY spend_usd DESC)                       AS spend_rank,
         SUM(spend_usd) OVER (ORDER BY spend_usd DESC
                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
           / SUM(spend_usd) OVER ()                                        AS cum_share
  FROM s
)
SELECT ranked.*,
       CASE WHEN cum_share - spend_usd / (SELECT SUM(spend_usd) FROM s) < 0.70 THEN 'A Strategic'
            WHEN cum_share - spend_usd / (SELECT SUM(spend_usd) FROM s) < 0.92 THEN 'B Core'
            ELSE 'C Tail' END                                            AS segment,
       CASE WHEN last_po_date < '2014-01-01' THEN 1 ELSE 0 END          AS inactive_18m,
       CASE WHEN po_count = 1 THEN 1 ELSE 0 END                          AS one_time
FROM ranked;

-- Segment summary
SELECT segment,
       COUNT(*)                                   AS suppliers,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM supplier_segments), 1)        AS pct_suppliers,
       ROUND(SUM(spend_usd) / 1e9, 2)             AS spend_b,
       ROUND(100.0 * SUM(spend_usd) / (SELECT SUM(spend_usd) FROM supplier_segments), 1) AS pct_spend,
       SUM(inactive_18m)                          AS inactive_18m,
       SUM(one_time)                              AS one_time,
       SUM(small_or_diverse)                      AS small_or_diverse
FROM supplier_segments
GROUP BY segment
ORDER BY segment;
