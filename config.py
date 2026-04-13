# ============================================================
# config.py — All settings in one place
#
# This file stores all the settings the project needs.
# If something needs to change (like the file path or model),
# you only change it HERE — not anywhere else.
# ============================================================

import os                    # lets us read environment variables
from dotenv import load_dotenv  # lets us read the .env file

# Read the .env file so we can use the values inside it
load_dotenv()

# ------------------------------------------------------------------
# YOUR GROQ API KEY
# This is your personal key to use the Groq AI service.
# Store it in the .env file — never paste it directly in code.
# ------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Which AI model to use (this one is fast and free)
GROQ_MODEL = "llama-3.3-70b-versatile"

# ------------------------------------------------------------------
# WHERE IS THE DATA FILE?
# ------------------------------------------------------------------
DATA_PATH = "data/battery_data.csv"

# ------------------------------------------------------------------
# COLUMN NAMES IN THE CSV FILE
# These are the exact column headers in your CSV.
# If your CSV has different column names, update the values here.
# ------------------------------------------------------------------
COL_SCENARIO      = "SCENARIO_NAME"    # which scenario: 'historical' or 'perfect'
COL_SCHEDULE      = "SCHEDULE_TYPE"    # 'cleared' (actual) or 'expected' (planned)
COL_DATETIME      = "START_DATETIME"   # when the interval started
COL_SOC           = "SOC"             # battery charge level (0=empty, 1=full)
COL_CHARGE        = "CHARGE_ENERGY"   # energy charged this interval (MWh)
COL_DISCHARGE     = "DISCHARGE_ENERGY" # energy discharged this interval (MWh)
COL_PRICE         = "PRICE_ENERGY"    # electricity price this interval ($/MWh)
COL_REVENUE       = "REVENUE_ENERGY"  # revenue earned this interval ($)

# ------------------------------------------------------------------
# SCENARIO NAMES (as they appear in the CSV)
# ------------------------------------------------------------------
HISTORICAL = "historical"   # how the battery actually ran
PERFECT    = "perfect"      # how it would run with perfect future knowledge

# Only look at 'cleared' rows (what actually happened, not what was planned)
CLEARED    = "cleared"

# ------------------------------------------------------------------
# AGENT SETTINGS
# ------------------------------------------------------------------
MAX_ROUNDS = 20    # stop the agent after this many tool calls (safety limit)
TOP_PRICES = 20    # look at this many high-price intervals for analysis
