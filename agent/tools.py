# ============================================================
# agent/tools.py — The 7 analysis tools
#
# HOW THIS FILE WORKS:
#   The AI cannot read the CSV file directly.
#   Instead, it calls these Python functions (called "tools").
#   Each tool does one specific job, like adding up revenue
#   or finding high-price moments.
#   The tool returns a simple summary — not raw data.
#
# THINK OF IT LIKE THIS:
#   The AI is a manager who asks a calculator (these tools)
#   to do the maths, then uses the results to write a report.
# ============================================================

import pandas as pd          # pandas helps us work with CSV/table data
import config                # our settings file

# This variable holds the loaded CSV data.
# It starts as None (empty) and gets filled when load_data() is called.
DATA = None


# ============================================================
# LOAD DATA — called once at the start to read the CSV file
# ============================================================

def load_data(file_path):
    """Read the CSV file and store it in the DATA variable."""

    global DATA   # we're changing the global DATA variable

    # Read the CSV file into a pandas DataFrame (like a spreadsheet in Python)
    DATA = pd.read_csv(file_path, parse_dates=[config.COL_DATETIME])

    # Make text columns lowercase so filtering works correctly
    # e.g. "Historical" and "historical" will be treated the same
    DATA[config.COL_SCENARIO] = DATA[config.COL_SCENARIO].str.strip().str.lower()
    DATA[config.COL_SCHEDULE] = DATA[config.COL_SCHEDULE].str.strip().str.lower()

    return DATA


def get_scenario_data(scenario_name):
    """
    Helper function: filter data to one scenario + only 'cleared' rows.

    Parameters:
        scenario_name: either "historical" or "perfect"

    Returns:
        A filtered table with only the rows we need
    """
    # Only keep rows where SCENARIO_NAME matches AND SCHEDULE_TYPE is 'cleared'
    filtered = DATA[
        (DATA[config.COL_SCENARIO] == scenario_name) &
        (DATA[config.COL_SCHEDULE] == config.CLEARED)
    ]
    return filtered


# ============================================================
# TOOL 1 — compute_revenue_summary
#
# WHAT IT ANSWERS: "How much did each scenario earn in total?
#                   And what is the gap between them?"
# ============================================================

def compute_revenue_summary():
    """
    Add up the total revenue for the historical and perfect scenarios.
    Calculate the gap (how much revenue was missed).
    """

    # Get the data for each scenario
    historical_rows = get_scenario_data(config.HISTORICAL)
    perfect_rows    = get_scenario_data(config.PERFECT)

    # Add up all the revenue numbers in each scenario
    historical_total = historical_rows[config.COL_REVENUE].sum()
    perfect_total    = perfect_rows[config.COL_REVENUE].sum()

    # The gap = how much MORE the perfect scenario earned
    gap = perfect_total - historical_total

    # Gap as a percentage of perfect revenue
    if perfect_total != 0:
        gap_percent = (gap / perfect_total) * 100
    else:
        gap_percent = 0

    # Find the date range from the data
    earliest_date = str(DATA[config.COL_DATETIME].min())
    latest_date   = str(DATA[config.COL_DATETIME].max())

    # Return a simple dictionary with all the results
    return {
        "historical_revenue":   round(historical_total, 2),
        "perfect_revenue":      round(perfect_total, 2),
        "gap":                  round(gap, 2),
        "gap_percent":          round(gap_percent, 2),
        "number_of_intervals":  len(historical_rows),
        "date_range":           earliest_date + " to " + latest_date,
    }


# ============================================================
# TOOL 2 — identify_high_price_intervals
#
# WHAT IT ANSWERS: "During the most expensive market moments,
#                   did the battery discharge and earn money?"
# ============================================================

def identify_high_price_intervals(top_n=20):
    """
    Find the top N most expensive price intervals in the day.
    Check how much each scenario discharged and earned during those moments.

    Parameters:
        top_n: how many top-price intervals to look at (default: 20)
    """

    historical_rows = get_scenario_data(config.HISTORICAL)
    perfect_rows    = get_scenario_data(config.PERFECT)

    # Sort the perfect scenario by price (highest first) and take the top N rows
    top_price_rows = perfect_rows.nlargest(top_n, config.COL_PRICE)

    # Get the timestamps of those top-price intervals
    top_timestamps = list(top_price_rows[config.COL_DATETIME])

    # Filter historical and perfect data to only those top-price timestamps
    hist_in_top = historical_rows[historical_rows[config.COL_DATETIME].isin(top_timestamps)]
    perf_in_top = perfect_rows[perfect_rows[config.COL_DATETIME].isin(top_timestamps)]

    # Count how many of those intervals each scenario was active (discharging)
    hist_active = int((hist_in_top[config.COL_DISCHARGE] > 0).sum())
    perf_active = int((perf_in_top[config.COL_DISCHARGE] > 0).sum())

    # Total revenue earned in those top-price intervals
    hist_revenue = round(float(hist_in_top[config.COL_REVENUE].sum()), 2)
    perf_revenue = round(float(perf_in_top[config.COL_REVENUE].sum()), 2)

    # Total MWh discharged in those intervals
    hist_mwh = round(float(hist_in_top[config.COL_DISCHARGE].sum()), 4)
    perf_mwh = round(float(perf_in_top[config.COL_DISCHARGE].sum()), 4)

    # Build a list of those intervals, one row per interval
    interval_list = []
    for _, row in top_price_rows.iterrows():
        timestamp = row[config.COL_DATETIME]

        # Find the historical and perfect rows for this timestamp
        h = historical_rows[historical_rows[config.COL_DATETIME] == timestamp]
        p = perfect_rows[perfect_rows[config.COL_DATETIME] == timestamp]

        interval_list.append({
            "datetime":            str(timestamp),
            "price":               round(float(row[config.COL_PRICE]), 2),
            "hist_discharged_mwh": round(float(h[config.COL_DISCHARGE].sum()), 4),
            "perf_discharged_mwh": round(float(p[config.COL_DISCHARGE].sum()), 4),
            "hist_revenue":        round(float(h[config.COL_REVENUE].sum()), 2),
            "perf_revenue":        round(float(p[config.COL_REVENUE].sum()), 2),
        })

    return {
        "top_n":                   top_n,
        "top_intervals":           interval_list,
        "hist_active_intervals":   hist_active,
        "perf_active_intervals":   perf_active,
        "hist_revenue_in_top":     hist_revenue,
        "perf_revenue_in_top":     perf_revenue,
        "hist_discharged_mwh":     hist_mwh,
        "perf_discharged_mwh":     perf_mwh,
    }


# ============================================================
# TOOL 3 — compare_dispatch
#
# WHAT IT ANSWERS: "How many times did each scenario charge or
#                   discharge? How different were they?"
# ============================================================

def compare_dispatch():
    """
    Compare the charging and discharging activity between
    the historical and perfect scenarios.
    Count how many times the two scenarios disagreed.
    """

    historical_rows = get_scenario_data(config.HISTORICAL)
    perfect_rows    = get_scenario_data(config.PERFECT)

    # --- Stats for the historical scenario ---
    hist_stats = {
        "total_charged_mwh":    round(float(historical_rows[config.COL_CHARGE].sum()), 4),
        "total_discharged_mwh": round(float(historical_rows[config.COL_DISCHARGE].sum()), 4),
        "charge_intervals":     int((historical_rows[config.COL_CHARGE] > 0).sum()),
        "discharge_intervals":  int((historical_rows[config.COL_DISCHARGE] > 0).sum()),
        "idle_intervals":       int(
            ((historical_rows[config.COL_CHARGE] == 0) &
             (historical_rows[config.COL_DISCHARGE] == 0)).sum()
        ),
    }

    # --- Stats for the perfect scenario ---
    perf_stats = {
        "total_charged_mwh":    round(float(perfect_rows[config.COL_CHARGE].sum()), 4),
        "total_discharged_mwh": round(float(perfect_rows[config.COL_DISCHARGE].sum()), 4),
        "charge_intervals":     int((perfect_rows[config.COL_CHARGE] > 0).sum()),
        "discharge_intervals":  int((perfect_rows[config.COL_DISCHARGE] > 0).sum()),
        "idle_intervals":       int(
            ((perfect_rows[config.COL_CHARGE] == 0) &
             (perfect_rows[config.COL_DISCHARGE] == 0)).sum()
        ),
    }

    # --- Find mismatches by joining both tables on timestamp ---
    # Rename columns so we can tell them apart after merging
    hist_slim = historical_rows[[config.COL_DATETIME, config.COL_CHARGE, config.COL_DISCHARGE]].copy()
    hist_slim = hist_slim.rename(columns={
        config.COL_CHARGE:    "h_charge",
        config.COL_DISCHARGE: "h_discharge",
    })

    perf_slim = perfect_rows[[config.COL_DATETIME, config.COL_CHARGE, config.COL_DISCHARGE]].copy()
    perf_slim = perf_slim.rename(columns={
        config.COL_CHARGE:    "p_charge",
        config.COL_DISCHARGE: "p_discharge",
    })

    # Merge the two tables side by side, matching on timestamp
    both = pd.merge(hist_slim, perf_slim, on=config.COL_DATETIME, how="inner")

    # Count mismatches
    # Missed discharge = perfect was discharging, historical was NOT
    missed_discharge_count = int(
        ((both["h_discharge"] == 0) & (both["p_discharge"] > 0)).sum()
    )
    # Extra discharge = historical was discharging, perfect was NOT (bad timing)
    extra_discharge_count = int(
        ((both["h_discharge"] > 0) & (both["p_discharge"] == 0)).sum()
    )
    # Missed charge = perfect was charging, historical was NOT
    missed_charge_count = int(
        ((both["h_charge"] == 0) & (both["p_charge"] > 0)).sum()
    )

    # How many MWh of discharge were missed in total?
    missed_rows = both[(both["h_discharge"] == 0) & (both["p_discharge"] > 0)]
    missed_mwh  = round(float(missed_rows["p_discharge"].sum()), 4)

    return {
        "historical": hist_stats,
        "perfect":    perf_stats,
        "mismatches": {
            "missed_discharge_intervals": missed_discharge_count,
            "extra_discharge_intervals":  extra_discharge_count,
            "missed_charge_intervals":    missed_charge_count,
            "missed_discharge_mwh":       missed_mwh,
            "net_discharge_gap_mwh":      round(
                perf_stats["total_discharged_mwh"] - hist_stats["total_discharged_mwh"], 4
            ),
        },
    }


# ============================================================
# TOOL 4 — analyze_state_of_charge
#
# WHAT IT ANSWERS: "Was the battery too full or too empty
#                   at key moments during the day?"
# SOC = State of Charge: 0 means empty, 1 means fully charged
# ============================================================

def analyze_state_of_charge(scenario="both"):
    """
    Look at the battery's charge level (SOC) throughout the day.

    Parameters:
        scenario: "historical", "perfect", or "both" (default)
    """

    # Decide which scenarios to analyse
    if scenario == "both":
        scenarios_to_check = [config.HISTORICAL, config.PERFECT]
    else:
        scenarios_to_check = [scenario]

    results = {}

    for sc in scenarios_to_check:
        rows = get_scenario_data(sc)

        if len(rows) == 0:
            results[sc] = {"error": "No data found for scenario: " + sc}
            continue

        soc_column = rows[config.COL_SOC]

        results[sc] = {
            "minimum_soc":          round(float(soc_column.min()), 4),
            "maximum_soc":          round(float(soc_column.max()), 4),
            "average_soc":          round(float(soc_column.mean()), 4),
            "soc_at_start_of_day":  round(float(rows.iloc[0][config.COL_SOC]), 4),
            "soc_at_end_of_day":    round(float(rows.iloc[-1][config.COL_SOC]), 4),
            # Near full = SOC above 95% (might block more charging)
            "near_full_intervals":  int((soc_column >= 0.95).sum()),
            # Near empty = SOC below 5% (might block discharging)
            "near_empty_intervals": int((soc_column <= 0.05).sum()),
            "total_intervals":      int(len(rows)),
        }

    return results


# ============================================================
# TOOL 5 — compute_revenue_by_period
#
# WHAT IT ANSWERS: "Which part of the day caused the biggest
#                   gap? Morning? Afternoon? Evening?"
# ============================================================

def compute_revenue_by_period(period_type="time_of_day"):
    """
    Break revenue into time-of-day buckets to see when the gap happened.

    Parameters:
        period_type: "hour" (groups by 0-23) or
                     "time_of_day" (off_peak / shoulder / peak)
    """

    historical_rows = get_scenario_data(config.HISTORICAL).copy()
    perfect_rows    = get_scenario_data(config.PERFECT).copy()

    if period_type == "hour":
        # Group by the hour of the day (0 = midnight, 23 = 11pm)
        historical_rows["period"] = historical_rows[config.COL_DATETIME].dt.hour
        perfect_rows["period"]    = perfect_rows[config.COL_DATETIME].dt.hour
        label = "hour_of_day"

    else:
        # Group into three buckets by time of day
        def assign_bucket(hour):
            if hour < 7 or hour >= 22:
                return "off_peak"    # night / early morning (usually cheap)
            if hour in (7, 8, 9, 17, 18, 19):
                return "shoulder"    # morning or evening transition
            return "peak"            # mid-day peak demand (usually expensive)

        historical_rows["period"] = historical_rows[config.COL_DATETIME].dt.hour.map(assign_bucket)
        perfect_rows["period"]    = perfect_rows[config.COL_DATETIME].dt.hour.map(assign_bucket)
        label = "time_of_day"

    # Sum revenue per period
    hist_by_period = historical_rows.groupby("period")[config.COL_REVENUE].sum().round(2).to_dict()
    perf_by_period = perfect_rows.groupby("period")[config.COL_REVENUE].sum().round(2).to_dict()

    # Join the two into one list of rows
    all_periods = sorted(set(list(hist_by_period.keys()) + list(perf_by_period.keys())), key=str)

    rows = []
    for period in all_periods:
        h = float(hist_by_period.get(period, 0))
        p = float(perf_by_period.get(period, 0))
        rows.append({
            label:            str(period),
            "historical_rev": round(h, 2),
            "perfect_rev":    round(p, 2),
            "gap":            round(p - h, 2),   # how much was missed in this period
        })

    return {
        "period_type": period_type,
        "breakdown":   rows,
        "total_hist":  round(sum(r["historical_rev"] for r in rows), 2),
        "total_perf":  round(sum(r["perfect_rev"]    for r in rows), 2),
    }


# ============================================================
# TOOL 6 — find_missed_opportunities
#
# WHAT IT ANSWERS: "Which exact moments cost the most money?
#                   When did perfect act but historical didn't?"
# ============================================================

def find_missed_opportunities(price_threshold=None):
    """
    Find every interval where:
      - The perfect battery was DISCHARGING (earning money)
      - The historical battery was IDLE (doing nothing)
      - The price was high enough to matter

    Parameters:
        price_threshold: minimum price to consider.
                         If not given, uses the 75th percentile automatically.
    """

    historical_rows = get_scenario_data(config.HISTORICAL)
    perfect_rows    = get_scenario_data(config.PERFECT)

    # Build a combined table with both scenarios side by side
    hist_slim = historical_rows[[
        config.COL_DATETIME, config.COL_DISCHARGE, config.COL_CHARGE,
        config.COL_REVENUE,  config.COL_PRICE
    ]].copy()
    hist_slim = hist_slim.rename(columns={
        config.COL_DISCHARGE: "h_discharge",
        config.COL_CHARGE:    "h_charge",
        config.COL_REVENUE:   "h_revenue",
        config.COL_PRICE:     "price",
    })

    perf_slim = perfect_rows[[
        config.COL_DATETIME, config.COL_DISCHARGE, config.COL_REVENUE
    ]].copy()
    perf_slim = perf_slim.rename(columns={
        config.COL_DISCHARGE: "p_discharge",
        config.COL_REVENUE:   "p_revenue",
    })

    # Merge on timestamp
    both = pd.merge(hist_slim, perf_slim, on=config.COL_DATETIME, how="inner")

    # Set the price threshold automatically if not provided
    if price_threshold is None:
        price_threshold = float(both["price"].quantile(0.75))

    # Find rows where: perfect discharged + historical was idle + price was high
    missed = both[
        (both["p_discharge"] > 0) &       # perfect was discharging
        (both["h_discharge"] == 0) &       # historical was NOT discharging
        (both["price"] >= price_threshold)  # price was high enough to care
    ].copy()

    # Calculate how much revenue was missed at each interval
    missed["revenue_missed"] = missed["p_revenue"] - missed["h_revenue"]

    # Get the 10 worst missed opportunities
    top10 = missed.nlargest(10, "revenue_missed")[[
        config.COL_DATETIME, "price", "p_discharge", "p_revenue", "h_revenue", "revenue_missed"
    ]].copy()
    top10[config.COL_DATETIME] = top10[config.COL_DATETIME].astype(str)
    top10 = top10.rename(columns={config.COL_DATETIME: "datetime"})

    return {
        "price_threshold_used":         round(price_threshold, 2),
        "total_missed_intervals":        int(len(missed)),
        "total_revenue_missed":          round(float(missed["revenue_missed"].sum()), 2),
        "perfect_discharged_mwh":        round(float(missed["p_discharge"].sum()), 4),
        "top_10_missed_opportunities":   top10.round(4).to_dict(orient="records"),
    }


# ============================================================
# TOOL 7 — compute_efficiency_ratio
#
# WHAT IT ANSWERS: "For every MWh of energy the battery moved,
#                   how much revenue did it earn?"
# Higher ratio = better price timing = smarter operation
# ============================================================

def compute_efficiency_ratio():
    """
    Calculate revenue per MWh for each scenario.
    This tells us whether the battery was active at good or bad price times.
    """

    results = {}

    for scenario in [config.HISTORICAL, config.PERFECT]:
        rows = get_scenario_data(scenario)

        total_revenue    = float(rows[config.COL_REVENUE].sum())
        total_discharged = float(rows[config.COL_DISCHARGE].sum())
        total_charged    = float(rows[config.COL_CHARGE].sum())
        total_dispatched = total_discharged + total_charged   # all energy moved

        # Revenue per MWh of all energy moved
        if total_dispatched > 0:
            rev_per_mwh_dispatched = round(total_revenue / total_dispatched, 4)
        else:
            rev_per_mwh_dispatched = 0

        # Revenue per MWh discharged only
        if total_discharged > 0:
            rev_per_mwh_discharged = round(total_revenue / total_discharged, 4)
        else:
            rev_per_mwh_discharged = 0

        results[scenario] = {
            "total_revenue":               round(total_revenue, 2),
            "total_discharged_mwh":        round(total_discharged, 4),
            "total_charged_mwh":           round(total_charged, 4),
            "revenue_per_mwh_dispatched":  rev_per_mwh_dispatched,
            "revenue_per_mwh_discharged":  rev_per_mwh_discharged,
        }

    # How much better is the perfect scenario?
    h = results[config.HISTORICAL]
    p = results[config.PERFECT]

    results["comparison"] = {
        "efficiency_gap_dispatched": round(
            p["revenue_per_mwh_dispatched"] - h["revenue_per_mwh_dispatched"], 4
        ),
        "efficiency_gap_discharged": round(
            p["revenue_per_mwh_discharged"] - h["revenue_per_mwh_discharged"], 4
        ),
    }

    return results


# ============================================================
# TOOL REGISTRY
#
# This dictionary maps each tool name (a string) to the actual
# Python function above.
# When the AI says "call compute_revenue_summary", this is how
# we look up which function to run.
# ============================================================

ALL_TOOLS = {
    "compute_revenue_summary":        compute_revenue_summary,
    "identify_high_price_intervals":  identify_high_price_intervals,
    "compare_dispatch":               compare_dispatch,
    "analyze_state_of_charge":        analyze_state_of_charge,
    "compute_revenue_by_period":      compute_revenue_by_period,
    "find_missed_opportunities":      find_missed_opportunities,
    "compute_efficiency_ratio":       compute_efficiency_ratio,
}


def run_tool(tool_name, arguments):
    """
    Look up a tool by name and run it with the given arguments.
    Returns the result, or an error message if something went wrong.
    """

    # Check if the tool exists
    if tool_name not in ALL_TOOLS:
        return {"error": "Tool not found: " + tool_name}

    # Try to run the tool and return the result
    try:
        result = ALL_TOOLS[tool_name](**arguments)
        return result
    except Exception as error:
        return {"error": "Tool failed: " + str(error)}
