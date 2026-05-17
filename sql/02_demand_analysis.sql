/*
 * ═══════════════════════════════════════════════════════════════
 * 02_DEMAND_ANALYSIS.sql
 * Analyze conversion demand patterns across channels,
 * brands, time periods, and funnel stages
 * ═══════════════════════════════════════════════════════════════
 */

.mode column
.headers on
.width 6 18 12 12 12 14

-- ─────────────────────────────────────────────────────────────
-- 2.1 CONVERSION FUNNEL: Drop-off rates per channel
-- ─────────────────────────────────────────────────────────────
SELECT '── 2.1 Conversion Funnel by Channel ──';

WITH funnel AS (
    SELECT
        Channel,
        SUM(CASE WHEN Event_Type = 'Impression' THEN 1 ELSE 0 END) AS Impressions,
        SUM(CASE WHEN Event_Type = 'Click' THEN 1 ELSE 0 END) AS Clicks,
        SUM(CASE WHEN Event_Type = 'Add-to-Cart' THEN 1 ELSE 0 END) AS AddToCart,
        SUM(CASE WHEN Event_Type = 'Purchase' THEN 1 ELSE 0 END) AS Purchases
    FROM touchpoints
    GROUP BY Channel
)
SELECT
    Channel,
    Impressions,
    Clicks,
    PRINTF('%.2f%%', Clicks * 100.0 / NULLIF(Impressions, 0)) AS CTR,
    AddToCart,
    PRINTF('%.2f%%', AddToCart * 100.0 / NULLIF(Clicks, 0)) AS Click_to_Cart,
    Purchases,
    PRINTF('%.2f%%', Purchases * 100.0 / NULLIF(AddToCart, 0)) AS Cart_to_Purchase,
    PRINTF('%.4f%%', Purchases * 100.0 / NULLIF(Impressions, 0)) AS Overall_CVR
FROM funnel
ORDER BY Purchases DESC;


-- ─────────────────────────────────────────────────────────────
-- 2.2 BRAND DEMAND RANKING: Conversions and conversion rate
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 2.2 Brand Demand Ranking ──';

WITH brand_stats AS (
    SELECT
        Brand_ID,
        COUNT(DISTINCT User_ID) AS Unique_Users,
        SUM(CASE WHEN Event_Type = 'Purchase' THEN 1 ELSE 0 END) AS Purchases,
        COUNT(*) AS Total_Events
    FROM touchpoints
    GROUP BY Brand_ID
)
SELECT
    Brand_ID,
    Unique_Users,
    Purchases,
    PRINTF('%.2f%%', Purchases * 100.0 / NULLIF(Unique_Users, 0)) AS Conv_Rate,
    PRINTF('%.1f', Total_Events * 1.0 / Unique_Users) AS Avg_Touchpoints,
    RANK() OVER (ORDER BY Purchases DESC) AS Demand_Rank
FROM brand_stats
ORDER BY Purchases DESC;


-- ─────────────────────────────────────────────────────────────
-- 2.3 CHANNEL DEMAND ELASTICITY: How spend relates to conversions
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 2.3 Channel Demand vs Spend ──';

WITH channel_conv AS (
    SELECT Brand_ID, Channel, COUNT(*) AS Purchases
    FROM touchpoints WHERE Event_Type = 'Purchase'
    GROUP BY Brand_ID, Channel
)
SELECT
    cs.Brand_ID,
    cs.Channel,
    PRINTF('₹%.2f Cr', cs.Total_Budget_Allocated / 10000000.0) AS Spend,
    COALESCE(cc.Purchases, 0) AS Conversions,
    CASE
        WHEN COALESCE(cc.Purchases, 0) > 0
        THEN PRINTF('%.1f', cc.Purchases * 10000000.0 / cs.Total_Budget_Allocated)
        ELSE '0.0'
    END AS Conv_Per_Crore,
    CASE
        WHEN COALESCE(cc.Purchases, 0) > 0 THEN
            CASE
                WHEN cc.Purchases * 10000000.0 / cs.Total_Budget_Allocated > 500 THEN '📈 HIGH ELASTICITY'
                WHEN cc.Purchases * 10000000.0 / cs.Total_Budget_Allocated > 100 THEN '📊 MODERATE'
                ELSE '📉 LOW ELASTICITY'
            END
        ELSE '⚫ ZERO RESPONSE'
    END AS Elasticity
FROM campaign_spend cs
LEFT JOIN channel_conv cc ON cs.Brand_ID = cc.Brand_ID AND cs.Channel = cc.Channel
ORDER BY cs.Brand_ID, Conv_Per_Crore DESC;


-- ─────────────────────────────────────────────────────────────
-- 2.4 MULTI-TOUCH JOURNEY LENGTH: Avg touchpoints before purchase
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 2.4 Average Journey Length Before Purchase ──';

WITH purchasers AS (
    SELECT DISTINCT User_ID, Brand_ID
    FROM touchpoints WHERE Event_Type = 'Purchase'
),
journey_lengths AS (
    SELECT
        t.Brand_ID,
        t.User_ID,
        COUNT(*) AS touchpoint_count,
        COUNT(DISTINCT t.Channel) AS channels_used
    FROM touchpoints t
    INNER JOIN purchasers p ON t.User_ID = p.User_ID AND t.Brand_ID = p.Brand_ID
    GROUP BY t.Brand_ID, t.User_ID
)
SELECT
    Brand_ID,
    COUNT(*) AS Purchasers,
    PRINTF('%.1f', AVG(touchpoint_count)) AS Avg_Touchpoints,
    MIN(touchpoint_count) AS Min_TP,
    MAX(touchpoint_count) AS Max_TP,
    PRINTF('%.1f', AVG(channels_used)) AS Avg_Channels_Used
FROM journey_lengths
GROUP BY Brand_ID
ORDER BY AVG(touchpoint_count) DESC;


-- ─────────────────────────────────────────────────────────────
-- 2.5 TOP CONVERSION PATHS: Most common channel sequences
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 2.5 Top 20 Conversion Paths ──';

WITH purchaser_journeys AS (
    SELECT
        t.User_ID,
        t.Brand_ID,
        GROUP_CONCAT(t.Channel, ' → ') AS journey_path
    FROM touchpoints t
    INNER JOIN (
        SELECT DISTINCT User_ID, Brand_ID
        FROM touchpoints WHERE Event_Type = 'Purchase'
    ) p ON t.User_ID = p.User_ID AND t.Brand_ID = p.Brand_ID
    WHERE t.Event_Type IN ('Impression', 'Click')
    GROUP BY t.User_ID, t.Brand_ID
)
SELECT
    journey_path AS Conversion_Path,
    COUNT(*) AS Frequency,
    PRINTF('%.2f%%', COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()) AS Pct
FROM purchaser_journeys
GROUP BY journey_path
ORDER BY COUNT(*) DESC
LIMIT 20;
