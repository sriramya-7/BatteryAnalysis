# 🔋 Battery Performance Analysis — AI Agent

> An AI agent that reads battery data, calls analysis tools step-by-step,
> and writes a clear performance report — all automatically.

---

## 🤔 What Does This Project Do?

A battery storage system can operate in two ways:

| Scenario | Meaning |
|---|---|
| **Historical** | How the battery *actually* operated |
| **Perfect** | How it *could have* operated with perfect knowledge of future prices |

This agent analyses the **gap between them** — how much revenue was missed and why —
then gives a battery trader **two clear recommendations** to improve future performance.

---

## 🏗️ How It Works (Plain English)

```
YOU RUN:  python main.py
                │
                ▼
  ┌─────────────────────────────┐
  │   main.py  (Start Here)     │
  │  • Loads the CSV data       │
  │  • Builds the question      │
  │  • Starts the AI agent      │
  └─────────────┬───────────────┘
                │
                ▼
  ┌─────────────────────────────┐
  │   agent.py  (The AI Brain)  │
  │  • Sends question to Groq   │
  │  • AI decides: call a tool  │
  │  • Gets result back         │
  │  • Repeats 7 times          │
  │  • Writes the final report  │
  └─────────────┬───────────────┘
                │ calls tools one by one
                ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │   tools.py  (The Data Analysts)                                 │
  │                                                                 │
  │  Tool 1 → compute_revenue_summary        "What is the gap?"    │
  │  Tool 2 → identify_high_price_intervals  "Did we miss spikes?" │
  │  Tool 3 → compare_dispatch               "How different?"      │
  │  Tool 4 → analyze_state_of_charge        "Was SOC a problem?"  │
  │  Tool 5 → find_missed_opportunities      "Which intervals?"    │
  │  Tool 6 → compute_efficiency_ratio       "Revenue per MWh?"    │
  │  Tool 7 → compute_revenue_by_period      "When did we lose?"   │
  └─────────────────────────────────────────────────────────────────┘
                │ all results
                ▼
  ┌─────────────────────────────┐
  │   report.txt  (The Output)  │
  │  • Revenue gap ($)          │
  │  • Primary driver           │
  │  • Secondary driver         │
  │  • 2 recommendations        │
  │  • Executive summary        │
  └─────────────────────────────┘
```

---

## 📁 File Guide

```
AssessmentProject2/
│
├── main.py           ← START HERE — runs everything
├── config.py         ← Settings (API key path, column names, model)
│
├── agent/
│   ├── agent.py      ← The AI loop (sends tools → gets results → writes report)
│   └── tools.py      ← The 7 analysis functions (all the pandas/data work)
│
├── data/
│   └── battery_data.csv   ← YOUR DATA FILE goes here (download separately)
│
├── .env              ← Your secret API key (never share this)
├── .env.example      ← Template — copy to .env and fill in your key
├── requirements.txt  ← Python packages needed
└── report.txt        ← Auto-created when you run main.py
```

> **Key idea:** The AI never reads the raw CSV. It only calls the tools in
> `tools.py` and gets back small, structured summaries. This makes the
> analysis reliable and auditable.

---

## ⚙️ Setup (One-Time, ~5 Minutes)

### Step 1 — Get a free Groq API key
1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up (free) and create an API key
3. Copy the key — you'll need it in Step 3

### Step 2 — Set up the project environment
```bash
# Create a virtual environment with Python 3.10
py -3.10 -m venv venv

# Activate it
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac / Linux

# Install required packages
pip install -r requirements.txt
```

### Step 3 — Add your API key
```bash
# Copy the template
copy .env.example .env
```
Open `.env` and replace `your_groq_api_key_here` with your actual key:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

### Step 4 — Add the data file
Download the battery CSV and save it to:
```
data/battery_data.csv
```

---

## ▶️ Running the Agent

```bash
# Standard run (shows all tool calls + final report)
venv\Scripts\python main.py

# Only show the final report (no tool-call trace)
venv\Scripts\python main.py --no-verbose

# Use a different CSV file
venv\Scripts\python main.py --data path/to/other_file.csv

# Save to a custom report file
venv\Scripts\python main.py --output my_report.txt
```

---

## 📋 What the Output Looks Like

```
🔋  Battery Performance Analysis Agent
    LLM Model : llama-3.3-70b-versatile
    Data file : data/battery_data.csv

────────────────────────────────────────────────
  Agent Round 1
────────────────────────────────────────────────
🔧  Calling tool: compute_revenue_summary
    Result: { historical_revenue: $3,240.80, perfect_revenue: $8,561.20, gap: $5,320.40 }

🔧  Calling tool: identify_high_price_intervals
    ...

✅  Agent finished — final report ready.

══════════════════════════════════════════════
=== BATTERY PERFORMANCE ANALYSIS REPORT ===

SECTION 1: PERFORMANCE GAP
  Historical Revenue : $3,240.80
  Perfect Revenue    : $8,561.20
  Performance Gap    : $5,320.40  (62.1% of perfect revenue)

SECTION 2: PRIMARY DRIVER
  Title: Missed High-Price Discharge Events
  ...

💾  Report saved to: report.txt
```

---

## 🔧 The 7 Tools (What Each One Does)

| # | Tool Name | Business Question It Answers |
|---|---|---|
| 1 | `compute_revenue_summary` | How large is the total $ gap? |
| 2 | `identify_high_price_intervals` | Did the battery discharge during price spikes? |
| 3 | `compare_dispatch` | How different were the charge/discharge patterns? |
| 4 | `analyze_state_of_charge` | Was the battery too full or too empty at key moments? |
| 5 | `find_missed_opportunities` | Which specific intervals cost the most money? |
| 6 | `compute_efficiency_ratio` | How much revenue was earned per MWh used? |
| 7 | `compute_revenue_by_period` | Which hours of the day caused the biggest gap? |

---

## ❓ Troubleshooting

| Error | Fix |
|---|---|
| `GROQ_API_KEY is not set` | Create `.env` from `.env.example` and add your key |
| `Data file not found` | Download the CSV and save to `data/battery_data.csv` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside the venv |
| Agent loops without finishing | Groq rate limit — wait 60s and try again |

---

## 🔄 Works on Any Dataset

The agent is not hardcoded to one file. It works on **any CSV with the same columns**:
- Change the file path with `--data your_file.csv`
- The prompt, date range, and scenario names are all read from the data automatically
- Column names can be updated in `config.py` if your CSV uses different headers

---

## 📦 Requirements

- **Python 3.10**
- **Groq API key** — free at [console.groq.com](https://console.groq.com)
- **battery_data.csv** — downloaded separately and placed in `data/`

---

## 🧠 Why This Approach?

The biggest mistake in LLM data analysis is dumping raw tables into the prompt.

| ❌ Bad Approach | ✅ This Approach |
|---|---|
| Send 288 rows × 8 columns to the AI | AI calls tools that summarise the data |
| AI makes arithmetic errors | Python/pandas does all calculations exactly |
| Hard to audit — black box | Every tool call is printed and traceable |
| Breaks on larger datasets | Scales to any dataset size |
| One giant prompt | Multi-step reasoning chain |
