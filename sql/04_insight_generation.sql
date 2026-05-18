/*
 * ═══════════════════════════════════════════════════════════════
 * 04_INSIGHT_GENERATION.sql
 * Strategic insights: revenue/volume trade-offs, channel
 * recommendations, budget reallocation signals, and
 * anomaly detection
 * ═══════════════════════════════════════════════════════════════
 */

.mode column
.headers on
.width 6 18 14 14 12 16

-- ─────────────────────────────────────────────────────────────
-- 4.1 REVENUE vs VOLUME TRADE-OFF
-- High CPA channels = premium/revenue play
-- Low CPA channels = volume play
-- ─────────────────────────────────────────────────────────────
SELECT '── 4.1 Revenue vs Volume Strategy Classification ──';

WITH channel_metrics AS (
    SELECT
        cs.Brand_ID,
        cs.Channel,
        cs.Total_Budget_Allocated AS Spend,
        COALESCE(p.Purchases, 0) AS Purchases,
        CASE
            WHEN COALESCE(p.Purchases, 0) > 0
            THEN cs.Total_Budget_Allocated / p.Purchases
            ELSE 999999999
        END AS CPA
    FROM campaign_spend cs
    LEFT JOIN (
        SELECT Brand_ID, Channel, COUNT(*) AS Purchases
        FROM touchpoints WHERE Event_Type = 'Purchase'
        GROUP BY Brand_ID, Channel
    ) p ON cs.Brand_ID = p.Brand_ID AND cs.Channel = p.Channel
),
brand_avg_cpa AS (
    SELECT Brand_ID, AVG(CASE WHEN CPA < 999999999 THEN CPA END) AS avg_cpa
    FROM channel_metrics GROUP BY Brand_ID
)
SELECT
    cm.Brand_ID,
    cm.Channel,
    PRINTF('₹%.0f', cm.CPA) AS CPA,
    cm.Purchases AS Volume,
    CASE
        WHEN cm.CPA > ba.avg_cpa * 1.5 THEN '💎 PREMIUM (Revenue Play)'
        WHEN cm.CPA < ba.avg_cpa * 0.5 THEN '📦 VOLUME (Scale Play)'
        ELSE '⚖️  BALANCED'
    END AS Strategy,
    CASE
        WHEN cm.CPA > ba.avg_cpa * 2 AND cm.Purchases < 50 THEN '🔴 DEFUND CANDIDATE'
        WHEN cm.CPA < ba.avg_cpa * 0.3 THEN '🟢 SCALE UP'
        ELSE '🟡 MAINTAIN'
    END AS Action
FROM channel_metrics cm
JOIN brand_avg_cpa ba ON cm.Brand_ID = ba.Brand_ID
WHERE cm.CPA < 999999999
ORDER BY cm.Brand_ID, cm.CPA;


-- ─────────────────────────────────────────────────────────────
-- 4.2 CHANNEL ROLE CLASSIFICATION
-- First-touch vs last-touch vs mid-funnel
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 4.2 Channel Role: Introducer / Influencer / Closer ──';

WITH user_journeys AS (
    SELECT
        User_ID,
        Brand_ID,
        Channel,
        ROW_NUMBER() OVER (PARTITION BY User_ID, Brand_ID ORDER BY Timestamp) AS touch_order,
        COUNT(*) OVER (PARTITION BY User_ID, Brand_ID) AS total_touches
    FROM touchpoints
    WHERE Event_Type IN ('Impression', 'Click')
),
role_counts AS (
    SELECT
        Channel,
        SUM(CASE WHEN touch_order = 1 THEN 1 ELSE 0 END) AS First_Touch,
        SUM(CASE WHEN touch_order > 1 AND touch_order < total_touches THEN 1 ELSE 0 END) AS Mid_Touch,
        SUM(CASE WHEN touch_order = total_touches AND total_touches > 1 THEN 1 ELSE 0 END) AS Last_Touch,
        COUNT(*) AS Total
    FROM user_journeys
    GROUP BY Channel
)
SELECT
    Channel,
    First_Touch,
    PRINTF('%.1f%%', First_Touch * 100.0 / Total) AS First_Pct,
    Mid_Touch,
    PRINTF('%.1f%%', Mid_Touch * 100.0 / Total) AS Mid_Pct,
    Last_Touch,
    PRINTF('%.1f%%', Last_Touch * 100.0 / Total) AS Last_Pct,
    CASE
        WHEN First_Touch * 1.0 / Total > 0.40 THEN '🚀 INTRODUCER'
        WHEN Last_Touch * 1.0 / Total > 0.35 THEN '🎯 CLOSER'
        ELSE '🔗 INFLUENCER'
    END AS Primary_Role
FROM role_counts
ORDER BY First_Touch DESC;


-- ─────────────────────────────────────────────────────────────
-- 4.3 BUDGET MISALLOCATION SIGNALS
-- Compare spend share vs conversion share
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 4.3 Budget Misallocation: Spend Share vs Conversion Share ──';

WITH spend_share AS (
    SELECT
        Brand_ID, Channel,
        Total_Budget_Allocated,
        Total_Budget_Allocated * 100.0 / SUM(Total_Budget_Allocated) OVER (PARTITION BY Brand_ID) AS spend_pct
    FROM campaign_spend
),
conv_share AS (
    SELECT
        Brand_ID, Channel,
        COUNT(*) AS Purchases,
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY Brand_ID) AS conv_pct
    FROM touchpoints WHERE Event_Type = 'Purchase'
    GROUP BY Brand_ID, Channel
)
SELECT
    ss.Brand_ID,
    ss.Channel,
    PRINTF('%.1f%%', ss.spend_pct) AS Spend_Share,
    PRINTF('%.1f%%', COALESCE(cs.conv_pct, 0)) AS Conv_Share,
    PRINTF('%+.1f pp', COALESCE(cs.conv_pct, 0) - ss.spend_pct) AS Gap,
    CASE
        WHEN COALESCE(cs.conv_pct, 0) - ss.spend_pct > 10 THEN '🟢 UNDER-INVESTED (increase)'
        WHEN COALESCE(cs.conv_pct, 0) - ss.spend_pct < -10 THEN '🔴 OVER-INVESTED (decrease)'
        ELSE '⚖️  ALIGNED'
    END AS Signal
FROM spend_share ss
LEFT JOIN conv_share cs ON ss.Brand_ID = cs.Brand_ID AND ss.Channel = cs.Channel
ORDER BY ss.Brand_ID, Gap;


-- ─────────────────────────────────────────────────────────────
-- 4.4 AD FATIGUE RISK: Channels with high impressions / low conv
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 4.4 Ad Fatigue Risk Channels ──';

WITH channel_efficiency AS (
    SELECT
        Brand_ID,
        Channel,
        SUM(CASE WHEN Event_Type = 'Impression' THEN 1 ELSE 0 END) AS Impressions,
        SUM(CASE WHEN Event_Type = 'Purchase' THEN 1 ELSE 0 END) AS Purchases,
        COUNT(DISTINCT User_ID) AS Users,
        SUM(CASE WHEN Event_Type = 'Impression' THEN 1.0 ELSE 0 END) /
            NULLIF(COUNT(DISTINCT User_ID), 0) AS Imp_Per_User
    FROM touchpoints
    GROUP BY Brand_ID, Channel
)
SELECT
    Brand_ID,
    Channel,
    Impressions,
    Purchases,
    PRINTF('%.1f', Imp_Per_User) AS Imp_Per_User,
    CASE
        WHEN Imp_Per_User > 10 AND (Purchases * 1.0 / NULLIF(Impressions, 0)) < 0.001
        THEN '🔴 HIGH FATIGUE RISK'
        WHEN Imp_Per_User > 5
        THEN '🟡 MODERATE RISK'
        ELSE '🟢 LOW RISK'
    END AS Fatigue_Risk,
    CASE
        WHEN Imp_Per_User > 10 THEN 'Cap at 8 imp/user'
        WHEN Imp_Per_User > 5 THEN 'Cap at 5 imp/user'
        ELSE 'No cap needed'
    END AS Recommendation
FROM channel_efficiency
WHERE Imp_Per_User > 3
ORDER BY Imp_Per_User DESC;


-- ─────────────────────────────────────────────────────────────
-- 4.5 FINAL STRATEGIC SUMMARY TABLE
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 4.5 Strategic Summary: Top Opportunities ──';

SELECT '';
SELECT '🟢 TOP 10 SCALE-UP OPPORTUNITIES (lowest CPA, highest volume potential):';
SELECT
    cs.Brand_ID,
    cs.Channel,
    PRINTF('₹%.2f Cr', cs.Total_Budget_Allocated / 10000000.0) AS Current_Spend,
    p.Purchases,
    PRINTF('₹%.0f', cs.Total_Budget_Allocated * 1.0 / p.Purchases) AS CPA
FROM campaign_spend cs
INNER JOIN (
    SELECT Brand_ID, Channel, COUNT(*) AS Purchases
    FROM touchpoints WHERE Event_Type = 'Purchase'
    GROUP BY Brand_ID, Channel
) p ON cs.Brand_ID = p.Brand_ID AND cs.Channel = p.Channel
WHERE p.Purchases > 0
ORDER BY cs.Total_Budget_Allocated * 1.0 / p.Purchases ASC
LIMIT 10;

SELECT '';
SELECT '🔴 TOP 10 DEFUND CANDIDATES (highest CPA, lowest efficiency):';
SELECT
    cs.Brand_ID,
    cs.Channel,
    PRINTF('₹%.2f Cr', cs.Total_Budget_Allocated / 10000000.0) AS Current_Spend,
    COALESCE(p.Purchases, 0) AS Purchases,
    CASE WHEN COALESCE(p.Purchases, 0) > 0
        THEN PRINTF('₹%.0f', cs.Total_Budget_Allocated * 1.0 / p.Purchases)
        ELSE '∞'
    END AS CPA
FROM campaign_spend cs
LEFT JOIN (
    SELECT Brand_ID, Channel, COUNT(*) AS Purchases
    FROM touchpoints WHERE Event_Type = 'Purchase'
    GROUP BY Brand_ID, Channel
) p ON cs.Brand_ID = p.Brand_ID AND cs.Channel = p.Channel
ORDER BY
    CASE WHEN COALESCE(p.Purchases, 0) = 0 THEN 999999999
         ELSE cs.Total_Budget_Allocated * 1.0 / p.Purchases END DESC
LIMIT 10;
