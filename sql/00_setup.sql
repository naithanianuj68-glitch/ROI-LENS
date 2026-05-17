/*
 * ═══════════════════════════════════════════════════════════════
 * PROJECT ROI LENS — Technical Codebase (Deliverable B)
 * Nexus Consumer Brands — Marketing Attribution SQL Analysis
 * ═══════════════════════════════════════════════════════════════
 *
 * Database: SQLite (load CSVs first using the setup script below)
 * Tables:   touchpoints, user_profiles, campaign_spend
 *
 * Run setup:  sqlite3 roi_lens.db < sql/00_setup.sql
 * Run all:    sqlite3 roi_lens.db < sql/01_price_bucketing.sql
 *             sqlite3 roi_lens.db < sql/02_demand_analysis.sql
 *             sqlite3 roi_lens.db < sql/03_segmentation.sql
 *             sqlite3 roi_lens.db < sql/04_insight_generation.sql
 * ═══════════════════════════════════════════════════════════════
 */

-- ═══════════════════════════════════════════════════════════════
-- 00_SETUP: Create tables and import CSV data
-- ═══════════════════════════════════════════════════════════════

.mode csv
.headers on

-- Create tables with proper schemas
CREATE TABLE IF NOT EXISTS touchpoints (
    User_ID       TEXT,
    Timestamp     TEXT,
    Campaign_ID   TEXT,
    Channel       TEXT,
    Event_Type    TEXT
);

CREATE TABLE IF NOT EXISTS user_profiles (
    User_ID        TEXT PRIMARY KEY,
    Segment        TEXT,
    Trend_Affinity TEXT,
    Geography      TEXT
);

CREATE TABLE IF NOT EXISTS campaign_spend (
    Campaign_ID            TEXT PRIMARY KEY,
    Brand_ID               TEXT,
    Channel                TEXT,
    Pricing_Model          TEXT,
    Cost_Rate_INR          REAL,
    Total_Budget_Allocated REAL
);

-- Import CSVs
.import --skip 1 data/touchpoints.csv touchpoints
.import --skip 1 data/user_profiles.csv user_profiles
.import --skip 1 data/campaign_spend.csv campaign_spend

-- Add derived Brand_ID column to touchpoints
ALTER TABLE touchpoints ADD COLUMN Brand_ID TEXT;
UPDATE touchpoints SET Brand_ID = SUBSTR(Campaign_ID, 5, 3);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tp_user ON touchpoints(User_ID);
CREATE INDEX IF NOT EXISTS idx_tp_brand ON touchpoints(Brand_ID);
CREATE INDEX IF NOT EXISTS idx_tp_channel ON touchpoints(Channel);
CREATE INDEX IF NOT EXISTS idx_tp_event ON touchpoints(Event_Type);
CREATE INDEX IF NOT EXISTS idx_cs_brand ON campaign_spend(Brand_ID);

SELECT '✅ Setup complete. Tables loaded:';
SELECT '   touchpoints:    ' || COUNT(*) || ' rows' FROM touchpoints;
SELECT '   user_profiles:  ' || COUNT(*) || ' rows' FROM user_profiles;
SELECT '   campaign_spend: ' || COUNT(*) || ' rows' FROM campaign_spend;
