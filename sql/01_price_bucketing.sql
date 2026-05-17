/*
 * ═══════════════════════════════════════════════════════════════
 * 01_PRICE_BUCKETING.sql
 * Bucket channels by cost efficiency and spend tiers
 * ═══════════════════════════════════════════════════════════════
 */

.mode column
.headers on
.width 6 18 12 14 14 16

-- ─────────────────────────────────────────────────────────────
-- 1.1 SPEND TIERS: Classify each brand-channel by spend level
-- ─────────────────────────────────────────────────────────────
SELECT '── 1.1 Spend Tier Classification ──';

SELECT
    Brand_ID,
    Channel,
    Pricing_Model,
    PRINTF('₹%.2f', Total_Budget_Allocated / 10000000.0) AS Spend_Cr,
    CASE
        WHEN Total_Budget_Allocated >= 40000000 THEN 'HEAVY (₹4Cr+)'
        WHEN Total_Budget_Allocated >= 20000000 THEN 'MEDIUM (₹2-4Cr)'
        WHEN Total_Budget_Allocated >= 5000000  THEN 'LIGHT (₹0.5-2Cr)'
        ELSE 'MINIMAL (<₹0.5Cr)'
    END AS Spend_Tier,
    PRINTF('%.1f%%', Total_Budget_Allocated * 100.0 / 
        SUM(Total_Budget_Allocated) OVER (PARTITION BY Brand_ID)) AS Pct_of_Brand
FROM campaign_spend
ORDER BY Brand_ID, Total_Budget_Allocated DESC;


-- ─────────────────────────────────────────────────────────────
-- 1.2 COST RATE BUCKETS: Compare CPC vs CPM pricing efficiency
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 1.2 Cost Rate Buckets (CPC vs CPM) ──';

SELECT
    Pricing_Model,
    Channel,
    COUNT(*) AS Num_Brands,
    PRINTF('₹%.2f', MIN(Cost_Rate_INR)) AS Min_Rate,
    PRINTF('₹%.2f', AVG(Cost_Rate_INR)) AS Avg_Rate,
    PRINTF('₹%.2f', MAX(Cost_Rate_INR)) AS Max_Rate,
    PRINTF('₹%.2f Cr', SUM(Total_Budget_Allocated) / 10000000.0) AS Total_Spend
FROM campaign_spend
GROUP BY Pricing_Model, Channel
ORDER BY Pricing_Model, AVG(Cost_Rate_INR) DESC;


-- ─────────────────────────────────────────────────────────────
-- 1.3 COST PER CONVERSION: Raw CPA by brand × channel
-- (using last-click as baseline before attribution adjustment)
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 1.3 Raw Cost Per Conversion (Last-Click) ──';

WITH purchases AS (
    SELECT Brand_ID, Channel, COUNT(*) AS purchase_count
    FROM touchpoints
    WHERE Event_Type = 'Purchase'
    GROUP BY Brand_ID, Channel
),
spend AS (
    SELECT Brand_ID, Channel, Total_Budget_Allocated
    FROM campaign_spend
)
SELECT
    s.Brand_ID,
    s.Channel,
    PRINTF('₹%.2f Cr', s.Total_Budget_Allocated / 10000000.0) AS Spend,
    COALESCE(p.purchase_count, 0) AS Purchases,
    CASE
        WHEN COALESCE(p.purchase_count, 0) > 0
        THEN PRINTF('₹%.0f', s.Total_Budget_Allocated * 1.0 / p.purchase_count)
        ELSE '∞ (no conv)'
    END AS CPA_INR,
    CASE
        WHEN COALESCE(p.purchase_count, 0) > 0 THEN
            CASE
                WHEN s.Total_Budget_Allocated / p.purchase_count < 5000 THEN '🟢 EFFICIENT'
                WHEN s.Total_Budget_Allocated / p.purchase_count < 20000 THEN '🟡 MODERATE'
                ELSE '🔴 EXPENSIVE'
            END
        ELSE '⚫ NO DATA'
    END AS Efficiency
FROM spend s
LEFT JOIN purchases p ON s.Brand_ID = p.Brand_ID AND s.Channel = p.Channel
ORDER BY s.Brand_ID, CPA_INR;


-- ─────────────────────────────────────────────────────────────
-- 1.4 SPEND CONCENTRATION: Herfindahl Index per brand
-- (measures how concentrated spend is across channels)
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 1.4 Spend Concentration (Herfindahl Index) ──';

WITH brand_totals AS (
    SELECT Brand_ID, SUM(Total_Budget_Allocated) AS total
    FROM campaign_spend GROUP BY Brand_ID
),
shares AS (
    SELECT
        cs.Brand_ID,
        cs.Channel,
        (cs.Total_Budget_Allocated / bt.total) AS share
    FROM campaign_spend cs
    JOIN brand_totals bt ON cs.Brand_ID = bt.Brand_ID
)
SELECT
    Brand_ID,
    PRINTF('%.4f', SUM(share * share)) AS HHI,
    CASE
        WHEN SUM(share * share) > 0.30 THEN '⚠️  HIGHLY CONCENTRATED'
        WHEN SUM(share * share) > 0.20 THEN '🟡 MODERATELY CONCENTRATED'
        ELSE '🟢 WELL DIVERSIFIED'
    END AS Concentration
FROM shares
GROUP BY Brand_ID
ORDER BY SUM(share * share) DESC;
