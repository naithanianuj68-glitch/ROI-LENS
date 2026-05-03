# 📊 Dataset — ROI Lens

Place the following 3 CSV files in this directory before running the notebook.

## Required Files

### 1. `touchpoints.csv`
Every user interaction with marketing channels.

| Column | Type | Description |
|--------|------|-------------|
| `User_ID` | string | Unique user identifier (e.g., `U_B01_00042`) |
| `Timestamp` | datetime | When the event occurred (e.g., `1/1/2026 19:27`) |
| `Campaign_ID` | string | Campaign identifier (e.g., `CMP_B01_INF_899`) — Brand_ID is extracted from this |
| `Channel` | string | One of: `Instagram`, `Google Search`, `Influencer Blog`, `YouTube`, `Marketplace` |
| `Event_Type` | string | One of: `Impression`, `Click`, `Add-to-Cart`, `Purchase` |

### 2. `user_profiles.csv`
Demographic and psychographic data per user.

| Column | Type | Description |
|--------|------|-------------|
| `User_ID` | string | Matches touchpoints.csv |
| `Segment` | string | `Gen-Z Trendseeker`, `Budget Parent`, `Fitness Enthusiast`, `Premium Gourmet` |
| `Trend_Affinity` | string | `Sustainable Packaging`, `Vegan`, `Value-Pack`, `Luxury`, `High-Protein` |
| `Geography` | string | `Tier 1`, `Tier 2`, `Tier 3` |

### 3. `campaign_spend.csv`
Budget allocation per brand per channel.

| Column | Type | Description |
|--------|------|-------------|
| `Campaign_ID` | string | Matches touchpoints.csv |
| `Brand_ID` | string | `B01` through `B10` |
| `Channel` | string | One of the 5 channels |
| `Pricing_Model` | string | `CPC` (cost per click) or `CPM` (cost per mille/thousand impressions) |
| `Cost_Rate_INR` | float | Cost rate in INR |
| `Total_Budget_Allocated` | float | Total budget allocated in INR |

## Data Characteristics
- **Bot traffic** is present and must be detected/removed
- **Ad fatigue patterns** exist (over-exposed users who don't convert)
- **Non-linear conversion paths** — users bounce between channels unpredictably
