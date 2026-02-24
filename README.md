<div align="center">

# 📈 Cornell Trading Competition 2023

### Multi-Case Algorithmic Trading Competition — Portfolio Optimization & VIX/SPX Options Strategies

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-1.5+-150458?logo=pandas)](https://pandas.pydata.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.23+-013243?logo=numpy)](https://numpy.org/)
[![PuLP](https://img.shields.io/badge/PuLP-LP%20Solver-orange)](https://coin-or.github.io/pulp/)
[![yFinance](https://img.shields.io/badge/yFinance-Market%20Data-blue)](https://github.com/ranaroussi/yfinance)

**A two-case quantitative trading competition: a margin-aware LP long-short equity portfolio (Case 1, code in this repo) and an algorithmic VIX/SPX options system exploiting their inverse correlation (Case 2).**

[Cornell Trading Competition](https://github.com/Shrey-Varma/CTC23) · [Strategy](#strategy) · [Implementation](#implementation)

</div>

---

## Overview

Built for the **Cornell Quantitative Trading Competition 2023**, this repo contains solutions to two independent competition cases:

### Case 1 — Long-Short Equity Portfolio Optimization (`case1_official.py`)

A margin-aware, daily-rebalancing **long-short equity portfolio** across 20 stocks in 4 markets (Brazil, Mexico, India, US). At each step, a Mixed-Integer Linear Program (MILP) maximizes expected return subject to dollar-neutrality, position limits, and a 25% turnover cap — operating on a **$1 million notional**.

### Case 2 — VIX/SPX Options Trading Strategy

An algorithmic options trading system targeting **VIX call and put derivatives** by exploiting the well-documented inverse correlation (~−0.7 to −0.8) between the S&P 500 (SPX) and the CBOE Volatility Index (VIX). SPX momentum signals drive directional positioning in VIX options: bearish SPX → long VIX calls; bullish SPX → long VIX puts. Position sizing and margin constraints are enforced throughout.

---

---

## Case 1 — Strategy & Implementation

### Portfolio Construction — Linear Programming

Daily expected returns per asset drive the MILP objective. A rolling window (first 7 days) initializes the momentum regime; subsequent signals are single-period open-to-close returns:

```
Expected Return(t) = (Close(t) - Open(t)) / Open(t)
```

### MILP Formulation

At each rebalancing step, the optimal portfolio weights are solved via a Linear Program (LP) using the [PuLP](https://coin-or.github.io/pulp/) solver:

**Objective:**
```
Maximize  Σ  r_i · (w_L_i − w_S_i)
           i
```
where `r_i` is the expected daily return, `w_L_i` is the long weight, and `w_S_i` is the short weight for asset `i`.

**Constraints:**

| Constraint | Description |
|---|---|
| `w_L_i ≤ δ_i` | Long weights gated by binary direction indicator |
| `w_S_i ≤ 1 − δ_i` | Can't simultaneously long and short the same asset |
| `Σ w_L_i = 0.5` | Long book fully invested (50% of portfolio) |
| `Σ w_S_i = 0.5` | Short book fully invested (50% of portfolio) |
| `Σ t_i ≤ 0.25` | Total turnover capped at 25% per period |
| `t_i ≥ \|Δw_i\|` | Turnover linearized via auxiliary variables |
| `w_L_i, w_S_i ∈ [0, 1]` | Weight bounds |
| `δ_i ∈ {0, 1}` | Binary direction variables (MILP) |

The **turnover constraint** (`Σ t_i ≤ 0.25`) enforces realistic trading costs — limiting total weight change per period to 25%, preventing excessive rebalancing that would erode returns.

---

## Implementation

### `get_stock_data(stock_list, start_date, end_date)`

Downloads OHLC data for 20 assets across 4 markets (Brazil, Mexico, India, US) using `yfinance`. Builds a hierarchical MultiIndex DataFrame `(Country, Stock, Metric)` and computes daily expected returns:

```python
expected_return = (close_price - open_price) / open_price
```

**Universe:**
```python
portfolio = {
    'BRA': ['PBR', 'VALE', 'ITUB', 'NU', 'BSBR'],       # Brazil
    'MEX': ['AMX', 'KCDMY', 'VLRS', 'ALFAA.MX', ...],   # Mexico
    'IND': ['RELIANCE.NS', 'TCS', 'HDB', 'INFY', ...],   # India
    'USA': ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'NVDA']      # US
}
```

### `get_weights(stock_data)`

Core engine: iterates day-by-day and solves the LP at each step.

```python
# Initialization: use first 7 days of returns for the first LP
# Subsequent days: use single-period return as signal

lp = pulp.LpProblem("Portfolio_Optimization", pulp.LpMaximize)
wL = pulp.LpVariable.dicts("Weights_Long", assets, lowBound=0, upBound=1)
wS = pulp.LpVariable.dicts("Weights_Short", assets, lowBound=0, upBound=1)
t  = pulp.LpVariable.dicts("Turnover", assets, lowBound=0, upBound=0.25)
delta = pulp.LpVariable.dicts("delta", assets, cat="Binary")

# Solve
lp.solve()
combined_weights = {asset: wL[asset].varValue - wS[asset].varValue for asset in assets}
```

The function returns two DataFrames:
- `weights` — optimal weights per asset per day
- `all_returns` — realized returns per asset per day

---

## Results

Sample output demonstrates optimal long-short allocations. The portfolio maintains market-neutrality (long book = short book = 50%) while maximizing expected returns within the turnover budget.

<div align="center">

| ![Portfolio Allocation — Day 1](sol1.png) | ![Portfolio Allocation — Day 2](sol2.png) |
|:---:|:---:|
| *Day 1 optimal weights* | *Day 2 optimal weights after rebalancing* |

</div>

---

## Installation & Usage

### Requirements

```bash
pip install pandas numpy yfinance pulp
```

### Run

```bash
python case1_official.py
```

The script fetches market data for Dec 10–30, 2021 and prints optimal portfolio weights at each rebalancing step.

### Configuration

Modify the `main()` function to change:
- **Portfolio universe** — add/remove tickers or markets
- **Date range** — `start` and `end` parameters for historical data
- **Turnover limit** — the `upBound=0.25` on `t` variables

---

## Case 2 — VIX/SPX Options Strategy

The second competition case targeted index derivatives. The strategy generates directional signals on SPX momentum and positions in VIX options accordingly:

| SPX Regime | VIX Options Position |
|---|---|
| **Bearish** (negative momentum) | Long VIX calls — volatility expected to spike |
| **Bullish** (positive momentum) | Long VIX puts — volatility expected to compress |

**Key design elements:**
- Momentum measured via rolling SPX Open-to-Close returns
- Margin-aware sizing: gross exposure capped relative to $1M notional
- Turnover constraints prevent over-trading around VIX spikes
- Inverse correlation (VIX/SPX ≈ −0.75) provides the statistical edge

---

## Key Engineering Decisions

### Mixed-Integer Linear Program (MILP)
Binary variables `δ_i` enforce the no-simultaneous-long-short constraint, making this a proper MILP rather than a simple LP. PuLP's CBC solver handles this via branch-and-bound.

### Margin-Aware Execution
The 50/50 long-short structure ensures the strategy maintains a dollar-neutral book — critical for regulatory margin requirements and minimizing market exposure.

### Turnover Linearization
The absolute-value constraint `t_i ≥ |w_new − w_old|` is linearized into two linear inequalities, preserving LP tractability while enforcing realistic transaction cost budgets.

---

## License

MIT — see [LICENSE](LICENSE) for details.
