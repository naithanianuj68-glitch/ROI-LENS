from nb_builder import md, code

def get_cells():
    return [
        md("---\n## Step 1 — Data Cleaning & Bot Removal\nParse timestamps, detect bots (fast clicks, high events w/ 0 purchases, repetitive patterns), remove them, and annotate ad fatigue."),

        code("""# Parse timestamps and sort chronologically per user
touchpoints['Timestamp'] = pd.to_datetime(touchpoints['Timestamp'], dayfirst=False)
touchpoints = touchpoints.sort_values(['User_ID','Timestamp']).reset_index(drop=True)

print(f"✅ Timestamps parsed. Range: {touchpoints['Timestamp'].min()} → {touchpoints['Timestamp'].max()}")
print(f"📊 Total records: {len(touchpoints):,}")
print(f"👤 Unique users: {touchpoints['User_ID'].nunique():,}")
"""),

        code("""# ═══════════════════════════════════════════════════════
# BOT DETECTION — Three criteria
# ═══════════════════════════════════════════════════════

# (a) Impossibly fast click sequences: median inter-event gap < 1 second
touchpoints['time_diff_sec'] = touchpoints.groupby('User_ID')['Timestamp'].diff().dt.total_seconds()
user_median_gap = touchpoints.groupby('User_ID')['time_diff_sec'].median()
fast_clickers = set(user_median_gap[user_median_gap < 1.0].dropna().index)
print(f"(a) Fast clickers (median gap < 1s): {len(fast_clickers):,} users")

# (b) High event count (>= 95th pctl) with zero purchases
user_evt_count = touchpoints.groupby('User_ID').size()
high_thresh = user_evt_count.quantile(0.95)
high_evt_users = set(user_evt_count[user_evt_count >= high_thresh].index)
purchasers = set(touchpoints[touchpoints['Event_Type']=='Purchase']['User_ID'].unique())
high_no_purchase = high_evt_users - purchasers
print(f"(b) High events (>={high_thresh:.0f}) with 0 purchases: {len(high_no_purchase):,} users")

# (c) Repetitive identical event-channel sequences (>80% same pattern)
touchpoints['evt_sig'] = touchpoints['Channel'] + '|' + touchpoints['Event_Type']
user_repetition = touchpoints.groupby('User_ID')['evt_sig'].agg(
    lambda x: x.value_counts().iloc[0] / len(x) if len(x) >= 5 else 0
)
repetitive_users = set(user_repetition[user_repetition > 0.8].index)
print(f"(c) Repetitive sequences (>80% same pair): {len(repetitive_users):,} users")

# Combine all bot users
bot_users = fast_clickers | high_no_purchase | repetitive_users
print(f"\\n🤖 Total unique bot users flagged: {len(bot_users):,}")
"""),

        code("""# Remove bot users
print(f"📊 BEFORE bot removal: {touchpoints['User_ID'].nunique():,} users | {len(touchpoints):,} records")
touchpoints_clean = touchpoints[~touchpoints['User_ID'].isin(bot_users)].copy()
touchpoints_clean.drop(columns=['time_diff_sec','evt_sig'], inplace=True)
print(f"📊 AFTER  bot removal: {touchpoints_clean['User_ID'].nunique():,} users | {len(touchpoints_clean):,} records")
removed = len(touchpoints) - len(touchpoints_clean)
print(f"🗑️  Removed: {removed:,} records ({removed/len(touchpoints)*100:.1f}%)")
"""),

        code("""# ═══════════════════════════════════════════════════════
# AD FATIGUE DETECTION
# Users with >= 95th percentile impressions to a channel WITHOUT converting
# ═══════════════════════════════════════════════════════

# Count impressions per user-channel
imp_counts = touchpoints_clean[touchpoints_clean['Event_Type']=='Impression'].groupby(
    ['User_ID','Channel']).size().reset_index(name='imp_count')

# Find user-channel pairs that converted
conv_pairs = touchpoints_clean[touchpoints_clean['Event_Type']=='Purchase'].groupby(
    ['User_ID','Channel']).size().reset_index(name='purch_count')

fatigue_df = imp_counts.merge(conv_pairs, on=['User_ID','Channel'], how='left')
fatigue_df['purch_count'] = fatigue_df['purch_count'].fillna(0)

# Non-converters with high impressions
non_conv = fatigue_df[fatigue_df['purch_count']==0]
p95 = non_conv['imp_count'].quantile(0.95)
fatigued = non_conv[non_conv['imp_count'] >= p95]

print(f"⚠️  Ad Fatigue Detection")
print(f"   95th pctl threshold: {p95:.0f} impressions without purchase")
print(f"   Fatigued user-channel pairs: {len(fatigued):,}")
print(f"\\n   Fatigue by channel:")
print(fatigued.groupby('Channel')['User_ID'].nunique().sort_values(ascending=False).to_string())

# Annotate fatigue via merge
fatigue_flags = fatigued[['User_ID','Channel']].drop_duplicates()
fatigue_flags['ad_fatigue'] = True
touchpoints_clean = touchpoints_clean.merge(fatigue_flags, on=['User_ID','Channel'], how='left')
touchpoints_clean['ad_fatigue'] = touchpoints_clean['ad_fatigue'].fillna(False)

print(f"\\n   Records flagged as fatigued: {touchpoints_clean['ad_fatigue'].sum():,}")
"""),
    ]
