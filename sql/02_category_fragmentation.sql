-- Step 2 · Spend cube by category: where is the supplier base most fragmented?
-- One row per UNSPSC family (category): spend, number of suppliers, and how much of
-- the category sits with tail suppliers. Many suppliers + small spend each = consolidation target.

DROP TABLE IF EXISTS category_cube;

CREATE TABLE category_cube AS
SELECT COALESCE(l.segment_title, 'Unclassified')               AS segment_title,
       COALESCE(l.family_title, 'Unclassified')                AS category,
       SUM(l.amount_usd)                                       AS spend_usd,
       COUNT(DISTINCT l.supplier_code)                         AS suppliers,
       COUNT(DISTINCT CASE WHEN s.segment = 'C Tail' THEN l.supplier_code END) AS tail_suppliers,
       SUM(CASE WHEN s.segment = 'C Tail' THEN l.amount_usd ELSE 0 END)       AS tail_spend_usd,
       COUNT(DISTINCT l.department_name)                       AS departments
FROM spend_lines l
JOIN supplier_segments s USING (supplier_code)
GROUP BY 1, 2;

-- Most fragmented categories: most suppliers, ranked
SELECT category,
       suppliers,
       tail_suppliers,
       ROUND(spend_usd / 1e6, 1)                    AS spend_m,
       ROUND(spend_usd / suppliers / 1e3, 0)        AS spend_per_supplier_k,
       ROUND(100.0 * tail_spend_usd / spend_usd, 1) AS pct_spend_in_tail
FROM category_cube
WHERE category <> 'Unclassified'
ORDER BY suppliers DESC
LIMIT 20;
