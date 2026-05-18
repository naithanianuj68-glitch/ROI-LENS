/*
 * ═══════════════════════════════════════════════════════════════
 * 03_SEGMENTATION.sql
 * Segment-specific analysis: conversion behavior by persona,
 * trend affinity, and geography tier
 * ═══════════════════════════════════════════════════════════════
 */

.mode column
.headers on
.width 20 18 10 10 12 14

-- ─────────────────────────────────────────────────────────────
-- 3.1 SEGMENT PERFORMANCE: Conversion rate by persona
-- ─────────────────────────────────────────────────────────────
SELECT '── 3.1 Conversion Rate by User Segment ──';

WITH segment_stats AS (
    SELECT
        up.Segment,
        COUNT(DISTINCT t.User_ID) AS Users,
        SUM(CASE WHEN t.Event_Type = 'Purchase' THEN 1 ELSE 0 END) AS Purchases,
        SUM(CASE WHEN t.Event_Type = 'Click' THEN 1 ELSE 0 END) AS Clicks,
        COUNT(*) AS Total_Events
    FROM touchpoints t
    INNER JOIN user_profiles up ON t.User_ID = up.User_ID
    GROUP BY up.Segment
)
SELECT
    Segment,
    Users,
    Purchases,
    PRINTF('%.2f%%', Purchases * 100.0 / NULLIF(Users, 0)) AS Conv_Rate,
    PRINTF('%.1f', Total_Events * 1.0 / Users) AS Avg_Events,
    PRINTF('%.2f%%', Clicks * 100.0 / NULLIF(Total_Events, 0)) AS Click_Rate,
    RANK() OVER (ORDER BY Purchases * 1.0 / NULLIF(Users, 0) DESC) AS Rank
FROM segment_stats
ORDER BY Conv_Rate DESC;


-- ─────────────────────────────────────────────────────────────
-- 3.2 SEGMENT × CHANNEL: Which channels work for which segments
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 3.2 Segment × Channel Conversion Matrix ──';

SELECT
    up.Segment,
    t.Channel,
    COUNT(DISTINCT t.User_ID) AS Users,
    SUM(CASE WHEN t.Event_Type = 'Purchase' THEN 1 ELSE 0 END) AS Purchases,
    PRINTF('%.2f%%',
        SUM(CASE WHEN t.Event_Type = 'Purchase' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(DISTINCT t.User_ID), 0)
    ) AS Conv_Rate
FROM touchpoints t
INNER JOIN user_profiles up ON t.User_ID = up.User_ID
GROUP BY up.Segment, t.Channel
ORDER BY up.Segment, Conv_Rate DESC;


-- ─────────────────────────────────────────────────────────────
-- 3.3 GEOGRAPHY TIER ANALYSIS: Performance by Tier 1/2/3
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 3.3 Geography Tier Performance ──';

WITH geo_stats AS (
    SELECT
        up.Geography,
        COUNT(DISTINCT t.User_ID) AS Users,
        SUM(CASE WHEN t.Event_Type = 'Impression' THEN 1 ELSE 0 END) AS Impressions,
        SUM(CASE WHEN t.Event_Type = 'Click' THEN 1 ELSE 0 END) AS Clicks,
        SUM(CASE WHEN t.Event_Type = 'Add-to-Cart' THEN 1 ELSE 0 END) AS AddToCart,
        SUM(CASE WHEN t.Event_Type = 'Purchase' THEN 1 ELSE 0 END) AS Purchases
    FROM touchpoints t
    INNER JOIN user_profiles up ON t.User_ID = up.User_ID
    GROUP BY up.Geography
)
SELECT
    Geography,
    Users,
    Purchases,
    PRINTF('%.2f%%', Purchases * 100.0 / NULLIF(Users, 0)) AS Conv_Rate,
    PRINTF('%.2f%%', Clicks * 100.0 / NULLIF(Impressions, 0)) AS CTR,
    PRINTF('%.2f%%', Purchases * 100.0 / NULLIF(AddToCart, 0)) AS Cart_Conv
FROM geo_stats
ORDER BY Geography;


-- ─────────────────────────────────────────────────────────────
-- 3.4 GEO × CHANNEL: Region-based channel effectiveness
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 3.4 Geography × Channel Effectiveness ──';

SELECT
    up.Geography,
    t.Channel,
    COUNT(DISTINCT t.User_ID) AS Users,
    SUM(CASE WHEN t.Event_Type = 'Purchase' THEN 1 ELSE 0 END) AS Purchases,
    PRINTF('%.2f%%',
        SUM(CASE WHEN t.Event_Type = 'Purchase' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(DISTINCT t.User_ID), 0)
    ) AS Conv_Rate
FROM touchpoints t
INNER JOIN user_profiles up ON t.User_ID = up.User_ID
GROUP BY up.Geography, t.Channel
ORDER BY up.Geography, Conv_Rate DESC;


-- ─────────────────────────────────────────────────────────────
-- 3.5 TREND AFFINITY: Purchase behavior by consumer trend
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 3.5 Trend Affinity Conversion Analysis ──';

SELECT
    up.Trend_Affinity,
    COUNT(DISTINCT t.User_ID) AS Users,
    SUM(CASE WHEN t.Event_Type = 'Purchase' THEN 1 ELSE 0 END) AS Purchases,
    PRINTF('%.2f%%',
        SUM(CASE WHEN t.Event_Type = 'Purchase' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(DISTINCT t.User_ID), 0)
    ) AS Conv_Rate,
    -- Which channel converts best for this affinity
    (SELECT t2.Channel
     FROM touchpoints t2
     INNER JOIN user_profiles up2 ON t2.User_ID = up2.User_ID
     WHERE up2.Trend_Affinity = up.Trend_Affinity AND t2.Event_Type = 'Purchase'
     GROUP BY t2.Channel
     ORDER BY COUNT(*) DESC LIMIT 1
    ) AS Best_Channel
FROM touchpoints t
INNER JOIN user_profiles up ON t.User_ID = up.User_ID
GROUP BY up.Trend_Affinity
ORDER BY Conv_Rate DESC;


-- ─────────────────────────────────────────────────────────────
-- 3.6 HIGH-VALUE SEGMENTS: Segment × Geography × Trend combos
-- ─────────────────────────────────────────────────────────────
SELECT '';
SELECT '── 3.6 Top 15 High-Value Micro-Segments ──';

SELECT
    up.Segment,
    up.Geography,
    up.Trend_Affinity,
    COUNT(DISTINCT t.User_ID) AS Users,
    SUM(CASE WHEN t.Event_Type = 'Purchase' THEN 1 ELSE 0 END) AS Purchases,
    PRINTF('%.2f%%',
        SUM(CASE WHEN t.Event_Type = 'Purchase' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(DISTINCT t.User_ID), 0)
    ) AS Conv_Rate
FROM touchpoints t
INNER JOIN user_profiles up ON t.User_ID = up.User_ID
GROUP BY up.Segment, up.Geography, up.Trend_Affinity
HAVING COUNT(DISTINCT t.User_ID) >= 100  -- minimum sample size
ORDER BY SUM(CASE WHEN t.Event_Type = 'Purchase' THEN 1.0 ELSE 0 END) / COUNT(DISTINCT t.User_ID) DESC
LIMIT 15;
