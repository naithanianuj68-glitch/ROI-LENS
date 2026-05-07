from nb_builder import md, code

def get_cells():
    return [
        md("""# 🔍 Project ROI Lens
## Marketing Attribution & Budget Optimization — Nexus Consumer Brands

**Objective:** Replace flawed last-click attribution with multi-touch models (Markov Chain + Shapley Value), model diminishing returns, and optimize ₹100 Crore budget across 10 brands × 5 channels.

| Item | Detail |
|------|--------|
| **Total Budget** | ₹100 Crore (₹10 Cr per brand) |
| **Channels** | Instagram, Google Search, Influencer Blog, YouTube, Marketplace |
| **Brands** | B01 – B10 |
| **Attribution** | Markov Chain + Shapley Value |
"""),

        md("---\n## Step 0 — Setup & Exploratory Data Analysis\nLoad all datasets, inspect schemas, and visualize key distributions."),

        code("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import curve_fit, minimize
from itertools import combinations
from math import factorial
from collections import Counter
import warnings, os, copy

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams.update({'figure.figsize':(14,8),'font.size':12,'figure.dpi':100,
                     'savefig.dpi':150,'savefig.bbox':'tight'})

os.makedirs('outputs/plots', exist_ok=True)
os.makedirs('outputs/csv', exist_ok=True)
print("✅ Libraries loaded. Output directories ready.")
"""),

        code("""# Load all three datasets
touchpoints = pd.read_csv('touchpoints.csv')
user_profiles = pd.read_csv('user_profiles.csv')
campaign_spend = pd.read_csv('campaign_spend.csv')

for name, df in [('touchpoints', touchpoints),('user_profiles', user_profiles),('campaign_spend', campaign_spend)]:
    print(f"\\n{'='*70}")
    print(f"📊 {name.upper()} — Shape: {df.shape}")
    print(f"{'='*70}")
    print(f"\\nDtypes:\\n{df.dtypes}")
    print(f"\\nFirst 5 rows:")
    display(df.head())
    print(f"\\nMissing values:\\n{df.isnull().sum()}")
"""),

        code("""# Extract Brand_ID from Campaign_ID for touchpoints
touchpoints['Brand_ID'] = touchpoints['Campaign_ID'].str.extract(r'(B\\d+)')

fig, axes = plt.subplots(2, 2, figsize=(18, 14))
fig.suptitle('Step 0 — Exploratory Data Analysis', fontsize=18, fontweight='bold', y=1.02)

# 1. Events per channel
ax = axes[0,0]
ch_counts = touchpoints['Channel'].value_counts()
bars = ax.bar(ch_counts.index, ch_counts.values, color=sns.color_palette("husl", len(ch_counts)), edgecolor='white')
ax.set_title('Events per Channel', fontweight='bold'); ax.set_ylabel('Count')
ax.tick_params(axis='x', rotation=25)
for b,v in zip(bars, ch_counts.values): ax.text(b.get_x()+b.get_width()/2, v+500, f'{v:,}', ha='center', fontweight='bold', fontsize=9)

# 2. Conversions per brand
ax = axes[0,1]
purch = touchpoints[touchpoints['Event_Type']=='Purchase']
brand_conv = purch['Brand_ID'].value_counts().sort_values(ascending=True)
brand_conv.plot(kind='barh', ax=ax, color=sns.color_palette("viridis", len(brand_conv)), edgecolor='white')
ax.set_title('Purchases per Brand', fontweight='bold'); ax.set_xlabel('# Purchases')

# 3. Spend breakdown by channel
ax = axes[1,0]
spend_ch = campaign_spend.groupby('Channel')['Total_Budget_Allocated'].sum().sort_values(ascending=False)
ax.pie(spend_ch, labels=spend_ch.index, autopct='%1.1f%%', startangle=90,
       colors=sns.color_palette("Set2", len(spend_ch)), wedgeprops={'edgecolor':'white','linewidth':2})
ax.set_title('Spend Breakdown by Channel', fontweight='bold')

# 4. Event type funnel
ax = axes[1,1]
evt_counts = touchpoints['Event_Type'].value_counts()
evt_colors = {'Impression':'#3498db','Click':'#2ecc71','Add-to-Cart':'#f39c12','Purchase':'#e74c3c'}
bars = ax.bar(evt_counts.index, evt_counts.values,
              color=[evt_colors.get(e,'#95a5a6') for e in evt_counts.index], edgecolor='white')
ax.set_title('Event Type Distribution', fontweight='bold'); ax.set_ylabel('Count')
for b,v in zip(bars, evt_counts.values): ax.text(b.get_x()+b.get_width()/2, v+500, f'{v:,}', ha='center', fontweight='bold', fontsize=9)

plt.tight_layout()
plt.savefig('outputs/plots/step0_eda.png')
plt.show()
print("📊 Saved: outputs/plots/step0_eda.png")
"""),
    ]
