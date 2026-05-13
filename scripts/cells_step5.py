from nb_builder import md, code

def get_cells():
    return [
        md("""---
## Step 5 — Budget Optimization (₹10 Crore per Brand)
For each brand, run **constrained optimization** (SLSQP) to maximize total attributed conversions using the fitted saturation curves. Each brand's total budget is fixed at ₹10 Crore.
"""),

        code("""# ═══════════════════════════════════════════════════════
# BUDGET OPTIMIZATION PER BRAND
# ═══════════════════════════════════════════════════════

BUDGET_PER_BRAND = 10e7  # ₹10 Crore = 10,00,00,000

optimization_results = {}

for b in brands:
    brand_channels = [ch for ch in channels if ch in saturation_params[b]]
    n_ch = len(brand_channels)

    # Objective: maximize conversions (minimize negative conversions)
    def neg_total_conversions(x):
        total = 0
        for i, ch in enumerate(brand_channels):
            p = saturation_params[b][ch]
            if x[i] > 0:
                total += hill_function(x[i], p['max_conv'], p['alpha'], p['k'])
        return -total

    # Constraint: total spend = ₹10 Crore
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - BUDGET_PER_BRAND}]

    # Bounds: each channel between ₹0 and ₹10 Crore
    bounds = [(0, BUDGET_PER_BRAND) for _ in range(n_ch)]

    # Initial guess: equal split
    x0 = np.full(n_ch, BUDGET_PER_BRAND / n_ch)

    # Run optimization
    result = minimize(neg_total_conversions, x0, method='SLSQP',
                     bounds=bounds, constraints=constraints,
                     options={'maxiter': 1000, 'ftol': 1e-12})

    # Current allocation
    brand_spend_data = campaign_spend[campaign_spend['Brand_ID']==b]
    current_alloc = {}
    for ch in brand_channels:
        row = brand_spend_data[brand_spend_data['Channel']==ch]
        current_alloc[ch] = row['Total_Budget_Allocated'].values[0] if len(row)>0 else 0

    # Calculate current conversions
    current_conv = sum(
        hill_function(current_alloc[ch], saturation_params[b][ch]['max_conv'],
                     saturation_params[b][ch]['alpha'], saturation_params[b][ch]['k'])
        for ch in brand_channels if current_alloc[ch] > 0
    )
    optimal_conv = -result.fun

    optimization_results[b] = {
        'channels': brand_channels,
        'current_alloc': current_alloc,
        'optimal_alloc': {ch: result.x[i] for i, ch in enumerate(brand_channels)},
        'current_conv': current_conv,
        'optimal_conv': optimal_conv,
        'lift_pct': ((optimal_conv - current_conv) / current_conv * 100) if current_conv > 0 else 0,
        'success': result.success
    }

print("✅ Optimization complete for all 10 brands.\\n")
"""),

        code("""# ═══════════════════════════════════════════════════════
# RESULTS: Current vs Optimized Allocation
# ═══════════════════════════════════════════════════════

opt_rows = []
for b in brands:
    res = optimization_results[b]
    print(f"\\n{'='*70}")
    print(f"Brand {b} — Budget Optimization (₹10 Crore)")
    print(f"{'='*70}")
    print(f"{'Channel':>20} | {'Current (₹Cr)':>14} | {'Current %':>10} | {'Optimal (₹Cr)':>14} | {'Optimal %':>10} | {'Change':>10}")
    print("─" * 95)

    total_current = sum(res['current_alloc'].values())
    for ch in res['channels']:
        curr = res['current_alloc'][ch]
        opt = res['optimal_alloc'][ch]
        curr_pct = curr / total_current * 100 if total_current > 0 else 0
        opt_pct = opt / BUDGET_PER_BRAND * 100
        change = "↑" if opt > curr * 1.05 else ("↓" if opt < curr * 0.95 else "≈")
        print(f"{ch:>20} | ₹{curr/1e7:>12.2f} | {curr_pct:>9.1f}% | ₹{opt/1e7:>12.2f} | {opt_pct:>9.1f}% | {change:>10}")

        opt_rows.append({
            'Brand_ID': b, 'Channel': ch,
            'Current_Spend_Cr': round(curr/1e7, 2), 'Current_Pct': round(curr_pct, 1),
            'Optimal_Spend_Cr': round(opt/1e7, 2), 'Optimal_Pct': round(opt_pct, 1)
        })

    print(f"\\n  Current conversions: {res['current_conv']:,.0f}")
    print(f"  Optimal conversions: {res['optimal_conv']:,.0f}")
    print(f"  Expected lift: {res['lift_pct']:+.1f}%")

opt_df = pd.DataFrame(opt_rows)
opt_df.to_csv('outputs/csv/optimal_budget.csv', index=False)
print(f"\\n💾 Saved: outputs/csv/optimal_budget.csv")
"""),

        code("""# ═══════════════════════════════════════════════════════
# SUMMARY TABLE: All 10 brands conversion lift
# ═══════════════════════════════════════════════════════

lift_rows = []
for b in brands:
    res = optimization_results[b]
    lift_rows.append({
        'Brand_ID': b,
        'Current_Conversions': round(res['current_conv']),
        'Projected_Conversions': round(res['optimal_conv']),
        'Lift_Pct': round(res['lift_pct'], 1)
    })

lift_df = pd.DataFrame(lift_rows)
print("\\n📊 Conversion Lift Summary — All 10 Brands:\\n")
display(lift_df)

total_curr = lift_df['Current_Conversions'].sum()
total_proj = lift_df['Projected_Conversions'].sum()
total_lift = (total_proj - total_curr) / total_curr * 100 if total_curr > 0 else 0

print(f"\\n🎯 TOTAL: {total_curr:,.0f} → {total_proj:,.0f} conversions ({total_lift:+.1f}% lift)")

# Visualization
fig, ax = plt.subplots(figsize=(14, 7))
x = np.arange(len(brands))
w = 0.35
ax.bar(x - w/2, lift_df['Current_Conversions'], w, label='Current', color='#e74c3c', edgecolor='white', alpha=0.85)
ax.bar(x + w/2, lift_df['Projected_Conversions'], w, label='Optimized', color='#2ecc71', edgecolor='white', alpha=0.85)
for i, row in lift_df.iterrows():
    ax.text(i + w/2, row['Projected_Conversions'] + 20, f"+{row['Lift_Pct']:.0f}%",
            ha='center', fontweight='bold', fontsize=10, color='#27ae60')
ax.set_xticks(x); ax.set_xticklabels(brands)
ax.set_ylabel('Conversions'); ax.set_title('Step 5 — Current vs Optimized Conversions per Brand', fontweight='bold', fontsize=16)
ax.legend(fontsize=12)
plt.tight_layout()
plt.savefig('outputs/plots/step5_optimization_lift.png')
plt.show()
print("📊 Saved: outputs/plots/step5_optimization_lift.png")
"""),
    ]
