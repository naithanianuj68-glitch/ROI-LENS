from nb_builder import md, code

def get_cells():
    return [
        md("""---
## Step 3 — True CPA & ROI Calculation
Merge attributed conversions with spend data. Compare **true multi-touch CPA** against flawed **last-click CPA**. Identify over-funded and under-funded channels.
"""),

        code("""# ═══════════════════════════════════════════════════════
# LAST-CLICK ATTRIBUTION (baseline for comparison)
# ═══════════════════════════════════════════════════════

# Last-click = 100% credit to the last channel before purchase
last_click_results = {}
for b in brands:
    brand_df = touchpoints_clean[touchpoints_clean['Brand_ID']==b].sort_values(['User_ID','Timestamp'])
    purchase_users = brand_df[brand_df['Event_Type']=='Purchase']['User_ID'].unique()
    last_clicks = {}
    for uid in purchase_users:
        user_events = brand_df[brand_df['User_ID']==uid]
        purch_idx = user_events[user_events['Event_Type']=='Purchase'].index
        if len(purch_idx) > 0:
            # Find the channel of the event just before purchase
            first_purch = purch_idx[0]
            pre_purchase = user_events[user_events.index < first_purch]
            if len(pre_purchase) > 0:
                last_ch = pre_purchase.iloc[-1]['Channel']
            else:
                last_ch = user_events.iloc[0]['Channel']
            last_clicks[uid] = last_ch
    lc_series = pd.Series(last_clicks)
    lc_counts = lc_series.value_counts()
    for ch in channels:
        if ch not in lc_counts: lc_counts[ch] = 0
    last_click_results[b] = lc_counts

print("✅ Last-click attribution computed for all brands.")
"""),

        code("""# ═══════════════════════════════════════════════════════
# MERGE WITH SPEND DATA & CALCULATE CPA/ROI
# ═══════════════════════════════════════════════════════

# Total conversions per brand
brand_total_conv = {}
for b in brands:
    brand_total_conv[b] = brand_journeys[b]['converted'].sum()

# Build summary table: brand × channel → spend, shapley_conv, true_cpa, lc_conv, lc_cpa, delta
summary_rows = []
for b in brands:
    total_conv = brand_total_conv[b]
    for ch in channels:
        # Spend from campaign_spend
        spend_row = campaign_spend[(campaign_spend['Brand_ID']==b) & (campaign_spend['Channel']==ch)]
        spend = spend_row['Total_Budget_Allocated'].values[0] if len(spend_row)>0 else 0

        # Shapley attributed conversions
        shapley_pct = shapley_df.loc[b, ch] / 100
        shapley_conv = shapley_pct * total_conv

        # Last-click conversions
        lc_conv = last_click_results[b].get(ch, 0)

        # True CPA (Shapley-based)
        true_cpa = spend / shapley_conv if shapley_conv > 0 else np.inf

        # Last-click CPA
        lc_cpa = spend / lc_conv if lc_conv > 0 else np.inf

        # ROI (using conversion count as proxy — each conversion = ₹5000 avg revenue)
        est_revenue = shapley_conv * 5000  # proxy revenue per conversion
        roi = ((est_revenue - spend) / spend * 100) if spend > 0 else 0

        summary_rows.append({
            'Brand_ID': b, 'Channel': ch, 'Spend_INR': spend,
            'Shapley_Conversions': round(shapley_conv, 1),
            'True_CPA_INR': round(true_cpa, 2),
            'LastClick_Conversions': lc_conv,
            'LastClick_CPA_INR': round(lc_cpa, 2) if lc_cpa != np.inf else np.inf,
            'CPA_Delta_INR': round(true_cpa - lc_cpa, 2) if (lc_cpa != np.inf and true_cpa != np.inf) else np.nan,
            'ROI_Pct': round(roi, 1)
        })

cpa_summary = pd.DataFrame(summary_rows)
print("📊 CPA & ROI Summary Table:")
display(cpa_summary)
cpa_summary.to_csv('outputs/csv/cpa_results.csv', index=False)
print("\\n💾 Saved: outputs/csv/cpa_results.csv")
"""),

        code("""# ═══════════════════════════════════════════════════════
# IDENTIFY OVER-FUNDED & UNDER-FUNDED CHANNELS PER BRAND
# ═══════════════════════════════════════════════════════

print("📊 Top 3 OVER-FUNDED channels per brand (highest True CPA = worst efficiency):\\n")
for b in brands:
    brand_cpa = cpa_summary[(cpa_summary['Brand_ID']==b) & (cpa_summary['True_CPA_INR'] < np.inf)]
    top3_over = brand_cpa.nlargest(3, 'True_CPA_INR')[['Channel','Spend_INR','True_CPA_INR','ROI_Pct']]
    print(f"  Brand {b}:")
    for _, row in top3_over.iterrows():
        print(f"    ❌ {row['Channel']:20s} | Spend: ₹{row['Spend_INR']:>14,.0f} | CPA: ₹{row['True_CPA_INR']:>10,.0f} | ROI: {row['ROI_Pct']:>6.1f}%")
    print()

print("\\n📊 Top 3 UNDER-FUNDED channels per brand (lowest True CPA = best efficiency):\\n")
for b in brands:
    brand_cpa = cpa_summary[(cpa_summary['Brand_ID']==b) & (cpa_summary['True_CPA_INR'] < np.inf)]
    top3_under = brand_cpa.nsmallest(3, 'True_CPA_INR')[['Channel','Spend_INR','True_CPA_INR','ROI_Pct']]
    print(f"  Brand {b}:")
    for _, row in top3_under.iterrows():
        print(f"    ✅ {row['Channel']:20s} | Spend: ₹{row['Spend_INR']:>14,.0f} | CPA: ₹{row['True_CPA_INR']:>10,.0f} | ROI: {row['ROI_Pct']:>6.1f}%")
    print()

# Flag negative ROI campaigns
neg_roi = cpa_summary[cpa_summary['ROI_Pct'] < 0]
print(f"\\n🚨 DEFUND CANDIDATES — Campaigns with NEGATIVE ROI: {len(neg_roi)}")
if len(neg_roi) > 0:
    display(neg_roi[['Brand_ID','Channel','Spend_INR','ROI_Pct','True_CPA_INR']].sort_values('ROI_Pct'))
else:
    print("   No negative-ROI campaigns found.")
"""),
    ]
