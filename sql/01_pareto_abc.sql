-- Step 5: Pareto / ABC segment per supplier
-- A = suppliers making up the first 70% of spend, B = next 22%, C = tail
WITH s AS (
  SELECT supplier_id, SUM(amount_usd) AS spend
  FROM spend_transactions
  GROUP BY supplier_id
), ranked AS (
  SELECT supplier_id, spend,
         SUM(spend) OVER (ORDER BY spend DESC) / SUM(spend) OVER () AS cum_share
  FROM s
)
SELECT supplier_id, spend, cum_share,
       CASE WHEN cum_share <= 0.70 THEN 'A Strategic'
            WHEN cum_share <= 0.92 THEN 'B Core'
            ELSE 'C Tail' END AS segment
FROM ranked;
