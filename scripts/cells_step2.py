from nb_builder import md, code

def get_cells():
    return [
        md("""---
## Step 2 — Multi-Touch Attribution Models
Build **Markov Chain** and **Shapley Value** attribution models, compare them side-by-side, and use Shapley as the primary method downstream.
"""),

        code("""# ═══════════════════════════════════════════════════════
# BUILD USER JOURNEY PATHS
# Each journey = sequence of channels from first touch to Purchase or No-Purchase
# ═══════════════════════════════════════════════════════

channels = sorted(touchpoints_clean['Channel'].unique())
brands = sorted(touchpoints_clean['Brand_ID'].unique())

def build_journeys(df, brand):
    \"\"\"Build channel journey paths for a given brand.\"\"\"
    brand_df = df[df['Brand_ID']==brand].sort_values(['User_ID','Timestamp'])
    journeys = []
    for uid, grp in brand_df.groupby('User_ID'):
        path = list(grp['Channel'].values)
        converted = 'Purchase' in grp['Event_Type'].values
        journeys.append({'user_id': uid, 'path': path, 'converted': converted})
    return pd.DataFrame(journeys)

# Build journeys for all brands
brand_journeys = {}
for b in brands:
    brand_journeys[b] = build_journeys(touchpoints_clean, b)
    conv_rate = brand_journeys[b]['converted'].mean()*100
    print(f"Brand {b}: {len(brand_journeys[b]):,} users, conv rate: {conv_rate:.1f}%")
"""),

        md("""### Method A — Markov Chain Attribution
Build transition probability matrices between channel states, then use the **removal effect** to attribute conversions:
- States: `Start → Channel₁ → Channel₂ → ... → Conversion / Null`
- For each channel, remove it and measure the drop in conversion probability
"""),

        code("""# ═══════════════════════════════════════════════════════
# MARKOV CHAIN ATTRIBUTION
# ═══════════════════════════════════════════════════════

def build_transition_matrix(journeys_df, channel_list):
    \"\"\"Build a transition probability matrix from journey paths.\"\"\"
    states = ['Start'] + channel_list + ['Conversion', 'Null']
    n = len(states)
    state_idx = {s:i for i,s in enumerate(states)}
    trans_count = np.zeros((n, n))

    for _, row in journeys_df.iterrows():
        path = row['path']
        converted = row['converted']
        # Add Start → first channel
        if len(path) > 0:
            trans_count[state_idx['Start'], state_idx[path[0]]] += 1
        # Add channel-to-channel transitions
        for i in range(len(path)-1):
            if path[i] in state_idx and path[i+1] in state_idx:
                trans_count[state_idx[path[i]], state_idx[path[i+1]]] += 1
        # Add last channel → Conversion/Null
        if len(path) > 0:
            end_state = 'Conversion' if converted else 'Null'
            trans_count[state_idx[path[-1]], state_idx[end_state]] += 1

    # Normalize rows to probabilities
    row_sums = trans_count.sum(axis=1, keepdims=True)
    row_sums[row_sums==0] = 1  # avoid division by zero
    trans_prob = trans_count / row_sums

    # Conversion and Null are absorbing states
    conv_idx = state_idx['Conversion']
    null_idx = state_idx['Null']
    trans_prob[conv_idx, :] = 0; trans_prob[conv_idx, conv_idx] = 1
    trans_prob[null_idx, :] = 0; trans_prob[null_idx, null_idx] = 1

    return trans_prob, states, state_idx


def calc_conversion_prob(trans_prob, state_idx, channel_list):
    \"\"\"Calculate steady-state conversion probability from Start using absorbing Markov chain.\"\"\"
    states_all = list(state_idx.keys())
    conv_idx = state_idx['Conversion']
    null_idx = state_idx['Null']
    absorbing = {conv_idx, null_idx}
    transient = [i for i in range(len(states_all)) if i not in absorbing]

    if len(transient) == 0:
        return 0.0

    # Q = transient-to-transient submatrix, R = transient-to-absorbing
    Q = trans_prob[np.ix_(transient, transient)]
    R = trans_prob[np.ix_(transient, list(absorbing))]

    # Fundamental matrix N = (I - Q)^(-1)
    try:
        N = np.linalg.inv(np.eye(len(transient)) - Q)
    except np.linalg.LinAlgError:
        return 0.0

    # Absorption probabilities B = N * R
    B = N @ R

    # Find Start index in transient states
    start_orig = state_idx['Start']
    if start_orig not in transient:
        return 0.0
    start_transient = transient.index(start_orig)

    # Conversion is first absorbing state (index 0 in absorbing list)
    absorbing_list = sorted(absorbing)
    conv_pos = absorbing_list.index(conv_idx)
    return B[start_transient, conv_pos]


def removal_effect(journeys_df, channel_list):
    \"\"\"Calculate removal effect for each channel.\"\"\"
    # Base conversion probability with all channels
    trans_prob, states, state_idx = build_transition_matrix(journeys_df, channel_list)
    base_prob = calc_conversion_prob(trans_prob, state_idx, channel_list)

    effects = {}
    for ch in channel_list:
        # Remove channel: filter out journeys that ONLY use this channel,
        # and remove this channel from all paths
        reduced_journeys = journeys_df.copy()
        reduced_journeys['path'] = reduced_journeys['path'].apply(
            lambda p: [c for c in p if c != ch]
        )
        # Remove empty paths (users who only interacted via this channel)
        reduced_journeys = reduced_journeys[reduced_journeys['path'].apply(len) > 0]

        if len(reduced_journeys) == 0:
            effects[ch] = 1.0  # removing this channel removes all conversions
            continue

        remaining_channels = [c for c in channel_list if c != ch]
        trans_r, states_r, idx_r = build_transition_matrix(reduced_journeys, remaining_channels)
        removed_prob = calc_conversion_prob(trans_r, idx_r, remaining_channels)

        # Removal effect = how much conversion prob drops
        if base_prob > 0:
            effects[ch] = (base_prob - removed_prob) / base_prob
        else:
            effects[ch] = 0.0

    return effects, base_prob

print("🔗 Markov Chain attribution functions defined.")
print("   Running for all 10 brands...")

markov_results = {}
for b in brands:
    effects, base_p = removal_effect(brand_journeys[b], channels)
    # Normalize to get attribution %
    total_effect = sum(effects.values())
    if total_effect > 0:
        attribution = {ch: effects[ch]/total_effect * 100 for ch in channels}
    else:
        attribution = {ch: 20.0 for ch in channels}
    markov_results[b] = attribution
    print(f"  Brand {b} (base conv prob: {base_p:.4f}): {', '.join(f'{ch}={v:.1f}%' for ch,v in attribution.items())}")

markov_df = pd.DataFrame(markov_results).T
markov_df.index.name = 'Brand_ID'
print("\\n✅ Markov Chain attribution complete.")
display(markov_df.round(2))
"""),

        md("""### Method B — Shapley Value Attribution
For each channel, calculate its **marginal contribution** across all possible coalitions of channels. The Shapley value provides a fair, game-theoretic allocation of credit.
"""),

        code("""# ═══════════════════════════════════════════════════════
# SHAPLEY VALUE ATTRIBUTION
# ═══════════════════════════════════════════════════════

def coalition_conversion_rate(journeys_df, coalition):
    \"\"\"Calculate conversion rate for journeys that pass through ANY channel in the coalition.\"\"\"
    if len(coalition) == 0:
        return 0.0
    coalition_set = set(coalition)
    # Filter to users who touched at least one channel in the coalition
    mask = journeys_df['path'].apply(lambda p: bool(set(p) & coalition_set))
    subset = journeys_df[mask]
    if len(subset) == 0:
        return 0.0
    return subset['converted'].mean()


def shapley_attribution(journeys_df, channel_list):
    \"\"\"Compute Shapley values for each channel.\"\"\"
    n = len(channel_list)
    shapley_values = {}

    for ch in channel_list:
        sv = 0.0
        others = [c for c in channel_list if c != ch]
        # Iterate over all possible subsets of other channels
        for size in range(0, n):
            for subset in combinations(others, size):
                subset_list = list(subset)
                # v(S ∪ {ch}) - v(S)
                with_ch = coalition_conversion_rate(journeys_df, subset_list + [ch])
                without_ch = coalition_conversion_rate(journeys_df, subset_list)
                marginal = with_ch - without_ch
                # Shapley weight
                weight = factorial(size) * factorial(n - size - 1) / factorial(n)
                sv += weight * marginal
        shapley_values[ch] = sv

    # Normalize to percentages
    total = sum(shapley_values.values())
    if total > 0:
        shapley_pct = {ch: v/total*100 for ch,v in shapley_values.items()}
    else:
        shapley_pct = {ch: 100/n for ch in channel_list}
    return shapley_pct

print("📐 Shapley Value attribution running for all 10 brands...")
print("   (5 channels → 2^5 = 32 subsets per channel — this may take a minute)\\n")

shapley_results = {}
for b in brands:
    shapley_pct = shapley_attribution(brand_journeys[b], channels)
    shapley_results[b] = shapley_pct
    print(f"  Brand {b}: {', '.join(f'{ch}={v:.1f}%' for ch,v in shapley_pct.items())}")

shapley_df = pd.DataFrame(shapley_results).T
shapley_df.index.name = 'Brand_ID'
print("\\n✅ Shapley Value attribution complete.")
display(shapley_df.round(2))
"""),

        code("""# ═══════════════════════════════════════════════════════
# SIDE-BY-SIDE COMPARISON: Markov vs Shapley
# ═══════════════════════════════════════════════════════

fig, axes = plt.subplots(2, 5, figsize=(28, 10))
fig.suptitle('Step 2 — Attribution Comparison: Markov Chain vs Shapley Value', fontsize=18, fontweight='bold')

for i, b in enumerate(brands):
    ax = axes[i//5, i%5]
    x = np.arange(len(channels))
    w = 0.35
    markov_vals = [markov_df.loc[b, ch] for ch in channels]
    shapley_vals = [shapley_df.loc[b, ch] for ch in channels]

    ax.bar(x - w/2, markov_vals, w, label='Markov', color='#3498db', edgecolor='white', alpha=0.85)
    ax.bar(x + w/2, shapley_vals, w, label='Shapley', color='#e74c3c', edgecolor='white', alpha=0.85)
    ax.set_title(f'Brand {b}', fontweight='bold', fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels([c[:8] for c in channels], rotation=45, fontsize=8)
    ax.set_ylabel('Attribution %')
    if i == 0: ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig('outputs/plots/step2_attribution_comparison.png')
plt.show()
print("📊 Saved: outputs/plots/step2_attribution_comparison.png")

# Save attribution scores
attr_combined = pd.concat([
    markov_df.reset_index().melt(id_vars='Brand_ID', var_name='Channel', value_name='Markov_Pct'),
    shapley_df.reset_index().melt(id_vars='Brand_ID', var_name='Channel', value_name='Shapley_Pct')[['Shapley_Pct']]
], axis=1)
attr_combined.to_csv('outputs/csv/attribution_scores.csv', index=False)
print("💾 Saved: outputs/csv/attribution_scores.csv")
"""),
    ]
