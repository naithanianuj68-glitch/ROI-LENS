# 🔍 Project ROI Lens

**Marketing Attribution & Budget Optimization for FMCG**

A data science project that replaces flawed last-click attribution with multi-touch models (Markov Chain + Shapley Value), models diminishing returns via saturation curves, and optimizes ₹100 Crore in marketing spend across 10 brands × 5 channels.

Built for **Nexus Consumer Brands** — a fictional FMCG company.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-orange?logo=jupyter&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Project Structure](#-project-structure)
- [Dataset](#-dataset)
- [Methodology](#-methodology)
- [Installation & Setup](#-installation--setup)
- [Usage](#-usage)
- [Outputs](#-outputs)
- [Key Findings](#-key-findings)
- [Tech Stack](#-tech-stack)
- [License](#-license)

---

## 🎯 Problem Statement

Nexus Consumer Brands spends **₹100 Crore/quarter** across 5 digital channels for 10 FMCG brands. Their current **last-click attribution** model gives 100% credit to the final touchpoint before purchase, which:

- **Over-credits** bottom-of-funnel channels (Marketplace, Google Search)
- **Under-credits** top-of-funnel channels (Instagram, YouTube, Influencer Blogs)
- Leads to **misallocated budgets** — starving channels that create awareness and intent

This project fixes attribution, identifies diminishing returns, and provides an **optimized ₹10 Crore budget allocation per brand**.

---

## 📁 Project Structure

```
roi-lens/
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── LICENSE                    # MIT License
├── .gitignore                 # Git ignore rules
│
├── roi_lens.ipynb             # 🔑 Main analysis notebook (34 cells, Steps 0-6)
│
├── data/                      # Input datasets (place CSVs here)
│   ├── README.md              # Data dictionary & instructions
│   ├── touchpoints.csv        # 566K user interaction events
│   ├── user_profiles.csv      # 100K user demographic profiles
│   └── campaign_spend.csv     # 50 rows of budget allocation
│
├── outputs/                   # Generated outputs (auto-created on run)
│   ├── csv/                   # Result tables
│   │   ├── attribution_scores.csv
│   │   ├── cpa_results.csv
│   │   ├── optimal_budget.csv
│   │   └── executive_budget_table.csv
│   └── plots/                 # Visualizations
│       ├── step0_eda.png
│       ├── step2_attribution_comparison.png
│       ├── step4_saturation_curves.png
│       └── step5_optimization_lift.png
│
└── scripts/                   # Notebook builder utilities (optional)
    ├── nb_builder.py
    ├── build_notebook.py
    └── cells_step0-6.py
```

---

## 📊 Dataset

> **Note:** Place the 3 CSV files in the `data/` directory before running the notebook.

| File | Rows | Description |
|------|------|-------------|
| `touchpoints.csv` | 566,510 | Every user interaction — impressions, clicks, add-to-carts, and purchases across 5 channels |
| `user_profiles.csv` | 100,000 | User demographics — segment, trend affinity, geography tier |
| `campaign_spend.csv` | 50 | Budget allocation — spend per brand per channel with CPC/CPM pricing |

### Channels
`Instagram` · `Google Search` · `Influencer Blog` · `YouTube` · `Marketplace`

### Brands
`B01` through `B10` (10 FMCG brands under Nexus Consumer Brands)

### User Segments
`Gen-Z Trendseeker` · `Budget Parent` · `Fitness Enthusiast` · `Premium Gourmet`

### Data Challenges (by design)
- 🤖 **Bot traffic** — automated click patterns mixed with real users
- 😴 **Ad fatigue** — users over-exposed to a channel without converting
- 🔀 **Non-linear conversion paths** — users bounce between channels unpredictably

---

## 🧠 Methodology

### Step 0 — Exploratory Data Analysis
Load datasets, inspect schemas, and visualize distributions (events per channel, conversions per brand, spend breakdown, conversion funnel).

### Step 1 — Data Cleaning & Bot Removal
- Detect bots via: (a) impossibly fast clicks (<1s gap), (b) high events + zero purchases, (c) repetitive identical patterns
- Remove bot users and annotate **ad fatigue** (95th percentile+ impressions without conversion)

### Step 2 — Multi-Touch Attribution
| Model | Approach | Use |
|-------|----------|-----|
| **Markov Chain** | Transition probability matrices + removal effect | Structural channel importance |
| **Shapley Value** | Game-theoretic fair credit allocation across all coalitions | **Primary model** for downstream analysis |

### Step 3 — True CPA & ROI
- Calculate Shapley-attributed CPA vs last-click CPA
- Identify over-funded and under-funded channels per brand
- Flag negative-ROI campaigns as defund candidates

### Step 4 — Diminishing Returns
Fit **Hill saturation curves** per brand × channel:
```
conversions = max_conv × spend^α / (spend^α + k^α)
```
Identifies channels past their saturation point where incremental spend is wasted.

### Step 5 — Budget Optimization
**Constrained optimization** (SLSQP) per brand:
- Maximize total conversions using saturation curves
- Constraint: total spend = ₹10 Crore per brand
- Bounds: ₹0 to ₹10 Crore per channel

### Step 6 — Executive Summary
CMO-ready report: channels to defund, channels to scale, frequency cap recommendations, total conversion lift, and final optimized budget table.

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9+
- Jupyter Notebook or JupyterLab

### Install dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/roi-lens.git
cd roi-lens

# Install required packages
pip install -r requirements.txt
```

### Add data files
Place your CSV files in the `data/` directory:
```
data/
├── touchpoints.csv
├── user_profiles.csv
└── campaign_spend.csv
```

---

## 💻 Usage

```bash
# Launch Jupyter
jupyter notebook roi_lens.ipynb
```

Run all cells sequentially (Kernel → Restart & Run All). The notebook will:
1. Load and explore the data
2. Clean bots and detect ad fatigue
3. Build Markov Chain and Shapley attribution models
4. Calculate true CPA/ROI and compare with last-click
5. Fit saturation curves and model diminishing returns
6. Optimize budget allocation per brand
7. Generate executive summary and save all outputs

---

## 📦 Outputs

### CSV Files (in `outputs/csv/`)
| File | Contents |
|------|----------|
| `attribution_scores.csv` | Markov + Shapley attribution % per brand × channel |
| `cpa_results.csv` | Spend, attributed conversions, True CPA, Last-Click CPA, ROI |
| `optimal_budget.csv` | Current vs optimized allocation per brand × channel |
| `executive_budget_table.csv` | Final CMO-ready budget table |

### Plots (in `outputs/plots/`)
| File | Contents |
|------|----------|
| `step0_eda.png` | EDA distribution plots |
| `step2_attribution_comparison.png` | Markov vs Shapley side-by-side (10 brands) |
| `step4_saturation_curves.png` | 50 Hill saturation curves (10 brands × 5 channels) |
| `step5_optimization_lift.png` | Current vs optimized conversions bar chart |

---

## 🔑 Key Findings

> These will be populated after running the notebook with your data.

- **Attribution gap**: Last-click systematically over-credits Marketplace/Google Search and under-credits Instagram/YouTube
- **Bot contamination**: ~X% of users flagged as bots, distorting attribution
- **Saturation**: Several brand-channel combinations are past their diminishing returns point
- **Optimization lift**: Reallocating the same ₹100 Crore yields **+X% more conversions**

---

## 🛠 Tech Stack

| Library | Purpose |
|---------|---------|
| `pandas` | Data manipulation and analysis |
| `numpy` | Numerical computing |
| `matplotlib` | Static visualizations |
| `seaborn` | Statistical plots |
| `scipy` | Curve fitting (`curve_fit`) and optimization (`minimize`) |
| `itertools` | Combinatorial operations for Shapley values |

No paid or uncommon libraries required.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

---

<p align="center">
  Built with ❤️ for smarter marketing spend decisions
</p>
