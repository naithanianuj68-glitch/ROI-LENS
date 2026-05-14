from nb_builder import md, code

def get_cells():
    return [
        md("""---
## Step 6 — Executive Summary
CMO-ready summary: channels to defund, channels to scale, frequency cap recommendations, total conversion lift, and the final brand-wise optimized budget table.
"""),

        code("""# ═══════════════════════════════════════════════════════
# CMO-READY EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════

print("=" * 80)
print("  📋 EXECUTIVE SUMMARY — Project ROI Lens")
print("  Nexus Consumer Brands — Marketing Attribution & Budget Optimization")
print("=" * 80)

# 1. CHANNELS TO DEFUND (worst ROI, highest CPA)
print("\\n\\n🔴 TOP 3 CHANNELS TO DEFUND (Worst ROI across all brands):")
print("─" * 60)
valid_cpa = cpa_summary[cpa_summary['True_CPA_INR'] < np.inf].copy()
worst_roi = valid_cpa.nsmallest(5, 'ROI_Pct').drop_duplicates('Channel').head(3)
for _, row in worst_roi.iterrows():
    # Calculate recommended reduction
    if row['Brand_ID'] in optimization_results:
        opt = optimization_results[row['Brand_ID']]['optimal_alloc'].get(row['Channel'], 0)
        curr = optimization_results[row['Brand_ID']]['current_alloc'].get(row['Channel'], 0)
        reduction = curr - opt
        print(f"  ❌ {row['Channel']:20s} (Brand {row['Brand_ID']})")
        print(f"     ROI: {row['ROI_Pct']:+.1f}% | CPA: ₹{row['True_CPA_INR']:,.0f}")
        print(f"     Recommended: Reduce by ₹{reduction/1e7:.2f} Crore")
    else:
        print(f"  ❌ {row['Channel']:20s} (Brand {row['Brand_ID']}) | ROI: {row['ROI_Pct']:+.1f}%")

# 2. CHANNELS TO INCREASE (best ROI, below saturation)
print("\\n\\n🟢 TOP 3 CHANNELS TO INCREASE SPEND (Best ROI, below saturation):")
print("─" * 60)
below_sat = []
for b in brands:
    brand_spend_data = campaign_spend[campaign_spend['Brand_ID']==b]
    for ch in channels:
        if ch in saturation_params.get(b, {}):
            p = saturation_params[b][ch]
            spend_row = brand_spend_data[brand_spend_data['Channel']==ch]
            actual_spend = spend_row['Total_Budget_Allocated'].values[0] if len(spend_row)>0 else 0
            if actual_spend < p['k']:  # below saturation
                roi_row = cpa_summary[(cpa_summary['Brand_ID']==b) & (cpa_summary['Channel']==ch)]
                if len(roi_row) > 0 and roi_row.iloc[0]['ROI_Pct'] > 0:
                    below_sat.append({'Brand_ID': b, 'Channel': ch,
                                      'ROI_Pct': roi_row.iloc[0]['ROI_Pct'],
                                      'Headroom_Cr': (p['k'] - actual_spend)/1e7})

below_sat_df = pd.DataFrame(below_sat)
if len(below_sat_df) > 0:
    top3_scale = below_sat_df.nlargest(3, 'ROI_Pct')
    for _, row in top3_scale.iterrows():
        opt = optimization_results[row['Brand_ID']]['optimal_alloc'].get(row['Channel'], 0)
        curr = optimization_results[row['Brand_ID']]['current_alloc'].get(row['Channel'], 0)
        increase = opt - curr
        print(f"  ✅ {row['Channel']:20s} (Brand {row['Brand_ID']})")
        print(f"     ROI: {row['ROI_Pct']:+.1f}% | Headroom: ₹{row['Headroom_Cr']:.2f} Cr before saturation")
        print(f"     Recommended: Increase by ₹{increase/1e7:.2f} Crore")

# 3. FREQUENCY CAP RECOMMENDATIONS
print("\\n\\n⚠️  FREQUENCY CAP RECOMMENDATIONS (Channels showing ad fatigue):")
print("─" * 60)
fatigue_by_ch = touchpoints_clean[touchpoints_clean['ad_fatigue']==True].groupby('Channel').size().sort_values(ascending=False)
if len(fatigue_by_ch) > 0:
    for ch, count in fatigue_by_ch.items():
        total_ch = len(touchpoints_clean[touchpoints_clean['Channel']==ch])
        pct = count / total_ch * 100
        # Recommend cap based on p95 threshold
        print(f"  ⚠️  {ch:20s}: {count:,} fatigued records ({pct:.1f}%)")
        print(f"     → Recommend frequency cap: {int(p95)} impressions/user/channel max")
else:
    print("  No significant ad fatigue detected.")

# 4. TOTAL CONVERSION LIFT
print("\\n\\n🎯 TOTAL EXPECTED CONVERSION LIFT FROM REALLOCATION:")
print("─" * 60)
print(f"  Current total conversions:   {total_curr:>10,.0f}")
print(f"  Projected total conversions: {total_proj:>10,.0f}")
print(f"  Net uplift:                  {total_proj - total_curr:>+10,.0f} ({total_lift:+.1f}%)")
"""),

        code("""# 5. BRAND-WISE OPTIMIZED BUDGET TABLE (₹10 Crore per brand)
print("\\n\\n📊 FINAL OPTIMIZED BUDGET TABLE — ₹10 Crore per Brand:")
print("═" * 100)

budget_table = []
for b in brands:
    res = optimization_results[b]
    row = {'Brand_ID': b}
    for ch in channels:
        if ch in res['optimal_alloc']:
            row[ch + '_Cr'] = round(res['optimal_alloc'][ch]/1e7, 2)
        else:
            row[ch + '_Cr'] = 0
    row['Total_Cr'] = sum(v for k,v in row.items() if k.endswith('_Cr'))
    row['Proj_Conversions'] = round(res['optimal_conv'])
    row['Lift_Pct'] = round(res['lift_pct'], 1)
    budget_table.append(row)

budget_df = pd.DataFrame(budget_table)
display(budget_df)

# Pretty print
print(f"\\n{'Brand':>6}", end="")
for ch in channels:
    print(f" | {ch[:12]:>12}", end="")
print(f" | {'Total':>8} | {'Lift':>6}")
print("─" * 100)
for _, row in budget_df.iterrows():
    print(f"{row['Brand_ID']:>6}", end="")
    for ch in channels:
        col = ch + '_Cr'
        print(f" | ₹{row[col]:>10.2f}", end="")
    print(f" | ₹{row['Total_Cr']:>6.2f} | {row['Lift_Pct']:>+5.1f}%")
print("─" * 100)
totals_row = budget_df[[c+'_Cr' for c in channels]].sum()
print(f"{'TOTAL':>6}", end="")
for ch in channels:
    print(f" | ₹{totals_row[ch+'_Cr']:>10.2f}", end="")
print(f" | ₹{totals_row.sum():>6.0f} | {total_lift:>+5.1f}%")
"""),

        md("""---
## ✅ Output Checklist & File Saves
All key outputs verified and saved:
"""),

        code("""# ═══════════════════════════════════════════════════════
# FINAL CHECKLIST
# ═══════════════════════════════════════════════════════

# Verify all CSV outputs
csv_files = {
    'outputs/csv/attribution_scores.csv': 'Markov + Shapley attribution scores',
    'outputs/csv/cpa_results.csv': 'True CPA & ROI per brand × channel',
    'outputs/csv/optimal_budget.csv': 'Optimized budget allocation',
}

# Save the executive budget table too
budget_df.to_csv('outputs/csv/executive_budget_table.csv', index=False)
csv_files['outputs/csv/executive_budget_table.csv'] = 'Final executive budget table'

# Verify all plot outputs
plot_files = {
    'outputs/plots/step0_eda.png': 'EDA distributions',
    'outputs/plots/step2_attribution_comparison.png': 'Markov vs Shapley comparison',
    'outputs/plots/step4_saturation_curves.png': 'Diminishing returns curves',
    'outputs/plots/step5_optimization_lift.png': 'Optimization lift chart',
}

print("=" * 70)
print("  ✅ PROJECT ROI LENS — OUTPUT CHECKLIST")
print("=" * 70)

print("\\n📁 CSV FILES:")
for path, desc in csv_files.items():
    exists = os.path.exists(path)
    icon = "✅" if exists else "❌"
    size = f"{os.path.getsize(path):,} bytes" if exists else "MISSING"
    print(f"  {icon} {path:50s} | {size:>12} | {desc}")

print("\\n🖼️  PLOT FILES:")
for path, desc in plot_files.items():
    exists = os.path.exists(path)
    icon = "✅" if exists else "❌"
    size = f"{os.path.getsize(path):,} bytes" if exists else "MISSING"
    print(f"  {icon} {path:50s} | {size:>12} | {desc}")

print("\\n" + "=" * 70)
all_exist = all(os.path.exists(p) for p in list(csv_files.keys()) + list(plot_files.keys()))
if all_exist:
    print("  🎉 ALL OUTPUTS VERIFIED — Project ROI Lens complete!")
else:
    print("  ⚠️  Some outputs are missing. Please re-run the relevant steps.")
print("=" * 70)
"""),
    ]
