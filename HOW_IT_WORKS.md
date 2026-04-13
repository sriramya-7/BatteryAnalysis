# How This Project Works — Plain English Guide

This document explains the project from the ground up.
No prior AI or Python experience needed.

---

## The Problem We're Solving

A battery storage system earns money by:
- **Charging** when electricity is cheap (buying low)
- **Discharging** when electricity is expensive (selling high)

We have two datasets for the same day:

```
HISTORICAL  →  What the battery actually did
PERFECT     →  What it should have done (with perfect future knowledge)
```

The gap between them is money left on the table.
Our job is to find **why** that gap exists and **how to close it**.

---

## Why Use an AI Agent?

The naive approach: paste all the data into ChatGPT and ask it to analyse.

**Why that fails:**
- The dataset has 288+ rows and 8 columns — too much for an LLM to count accurately
- LLMs hallucinate numbers when doing maths on large tables
- You can't verify where the numbers came from

**What we do instead:**
- Keep the AI in charge of **thinking and reasoning**
- Let Python tools handle **all the maths**
- The AI only sees small, accurate summaries — never raw data

---

## The Three Files That Matter

### 1. `main.py` — The Starter

Think of this as the "on" button.

When you run `python main.py`, it:
1. Checks your API key is set
2. Checks the CSV file exists
3. Loads the data
4. Builds a plain-English question from the data
5. Hands the question to the agent
6. Prints and saves the report

---

### 2. `agent/tools.py` — The Data Analysts

This file contains 7 Python functions (called "tools").

Each tool does one specific job on the battery data and returns a summary:

```
compute_revenue_summary()
  → Adds up all revenue for both scenarios
  → Returns: { historical: $3,240, perfect: $8,561, gap: $5,320 }

identify_high_price_intervals(top_n=20)
  → Finds the 20 most expensive market moments
  → Checks if the battery discharged during those moments
  → Returns: a list of intervals with prices and discharge amounts

compare_dispatch()
  → Counts how many times the battery charged/discharged in each scenario
  → Finds mismatches (battery was idle when it should have been active)
  → Returns: mismatch counts and total MWh differences

analyze_state_of_charge(scenario="both")
  → Looks at the battery's charge level (SOC) throughout the day
  → SOC = 0 means empty, 1 means fully charged
  → Returns: min, max, average SOC and any constraint violations

find_missed_opportunities()
  → Finds every interval where perfect battery earned money but historical didn't
  → Returns: total $ missed and the top 10 worst moments

compute_efficiency_ratio()
  → Calculates: revenue ÷ MWh used  (like miles per gallon, but for batteries)
  → Returns: efficiency score for each scenario

compute_revenue_by_period(period_type="time_of_day")
  → Groups revenue by off-peak / shoulder / peak periods
  → Returns: revenue table showing where the gap comes from
```

---

### 3. `agent/agent.py` — The AI Brain

This file runs a back-and-forth conversation between the AI and the tools:

```
ROUND 1:
  AI thinks: "I need to know the revenue gap first."
  AI calls:  compute_revenue_summary()
  Tool says: { gap: $5,320, gap_pct: 62.1% }
  AI thinks: "Big gap. Now let me check price intervals..."

ROUND 2:
  AI calls:  identify_high_price_intervals(top_n=20)
  Tool says: { hist_active_count: 4, perf_active_count: 18, ... }
  AI thinks: "Historical only discharged in 4 of 20 spikes. That's the issue."

... continues for all 7 tools ...

ROUND 8:
  AI has all the evidence it needs.
  AI writes: The final structured report.
  Done!
```

This loop is called a **ReAct loop** (Reason → Act → Observe → Reason again).

---

## What the AI Can and Cannot Do

| ✅ The AI CAN | ❌ The AI CANNOT |
|---|---|
| Decide which tool to call next | Read the raw CSV file |
| Reason about tool results | Do arithmetic on raw numbers |
| Identify patterns across tool outputs | Invent numbers not from tools |
| Write clear, structured reports | Skip a tool and guess |
| Explain causes and give recommendations | Give generic advice (rules prevent it) |

---

## The Flow in One Picture

```
                     ┌──────────────┐
   python main.py ──►│   main.py    │
                     │ loads data   │
                     │ builds prompt│
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  agent.py    │◄────────────────────┐
                     │  AI (Groq)   │                     │
                     │  decides:    │                     │
                     │  call a tool │                     │
                     └──────┬───────┘                     │
                            │                             │
                            ▼                             │
                     ┌──────────────┐              tool result
                     │  tools.py    │              goes back
                     │  runs maths  │──────────────────────┘
                     │  on the CSV  │
                     └──────────────┘

  (this loop runs 7 times — once per tool)

                            │
                            ▼ after all tools done

                     ┌──────────────┐
                     │  report.txt  │
                     │  Final report│
                     │  saved here  │
                     └──────────────┘
```

---

## Config — One File to Rule Them All

The `config.py` file stores every setting:

```python
GROQ_API_KEY  →  Your secret API key (loaded from .env)
GROQ_MODEL    →  Which AI model to use
DATA_PATH     →  Where to find the CSV file
COLUMNS       →  Column names in the CSV (change here if CSV headers differ)
SCENARIO_*    →  What the scenario names are called in the CSV
MAX_ITERATIONS → Maximum tool-call rounds (safety limit)
```

If you want to use a different dataset, you only need to update `config.py`.

---

## Glossary

| Term | Plain English Meaning |
|---|---|
| **SOC** (State of Charge) | Battery fill level — 0% = empty, 100% = full |
| **Dispatch** | The act of charging or discharging the battery |
| **Cleared** | What actually happened (vs. "expected" = what was planned) |
| **Interval** | A 5-minute time slot in the data |
| **Tool** | A Python function the AI is allowed to call |
| **Agent** | An AI that can call tools and make decisions |
| **ReAct loop** | The cycle of: think → act → observe → think again |
| **LLM** | Large Language Model (e.g. the AI inside Groq) |
| **Groq** | The fast AI inference platform we use to run the LLM |
| **$/MWh** | Price of electricity per megawatt-hour (the unit) |
| **Revenue gap** | Perfect revenue minus historical revenue |
