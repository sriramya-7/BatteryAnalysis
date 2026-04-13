# ============================================================
# main.py — Start here. This runs everything.
#
# WHAT HAPPENS WHEN YOU RUN THIS FILE:
#   1. Check you have an API key set up
#   2. Check the data file exists
#   3. Load the CSV data
#   4. Show a summary of what's in the data
#   5. Ask the AI agent to analyse the data
#   6. Print the final report on screen
#   7. Save the report to a file
#
# HOW TO RUN:
#   python main.py
# ============================================================

import os               # lets us check if files exist
import sys              # lets us exit the program early with an error
from datetime import datetime   # used to add a timestamp to the saved report

import config                      # our settings file
from agent.tools import load_data  # the function that reads the CSV
from agent.agent import run_agent  # the function that runs the AI agent


# ============================================================
# STEP 1 — Check that the API key is set up
# ============================================================

def check_api_key():
    """Stop the program early if the Groq API key is missing."""

    if not config.GROQ_API_KEY:
        # Print a helpful message and stop
        print("")
        print("❌  ERROR: Your Groq API key is not set!")
        print("")
        print("   How to fix:")
        print("   1. Open the file called  .env  in your project folder")
        print("   2. Replace  your_groq_api_key_here  with your real key")
        print("   3. Get a free key at: https://console.groq.com")
        print("")
        sys.exit(1)   # stop the program


# ============================================================
# STEP 2 — Check that the data file exists
# ============================================================

def check_data_file():
    """Stop the program early if the CSV data file is not found."""

    if not os.path.exists(config.DATA_PATH):
        print("")
        print("❌  ERROR: Data file not found!")
        print("   Expected location: " + config.DATA_PATH)
        print("")
        print("   How to fix:")
        print("   1. Download the battery CSV file")
        print("   2. Save it to: " + config.DATA_PATH)
        print("")
        sys.exit(1)


# ============================================================
# STEP 3 — Load and show a summary of the data
# ============================================================

def load_and_show_data():
    """Load the CSV and print a summary of what's inside."""

    print("   Loading data from: " + config.DATA_PATH)

    # Load the CSV file (this fills the DATA variable in tools.py)
    data = load_data(config.DATA_PATH)

    # Print a quick summary so you know what was loaded
    print("")
    print("=" * 55)
    print("  DATA LOADED SUCCESSFULLY")
    print("=" * 55)
    print("  Total rows   : " + str(len(data)))

    # Show the date range
    earliest = str(data[config.COL_DATETIME].min())
    latest   = str(data[config.COL_DATETIME].max())
    print("  Date range   : " + earliest + "  to  " + latest)

    # Show what scenarios are in the data
    scenarios = sorted(data[config.COL_SCENARIO].unique().tolist())
    print("  Scenarios    : " + str(scenarios))

    # Show what schedule types are in the data
    schedules = sorted(data[config.COL_SCHEDULE].unique().tolist())
    print("  Schedules    : " + str(schedules))

    print("=" * 55)
    print("")

    return data


# ============================================================
# STEP 4 — Build the question to send to the AI agent
# ============================================================

def build_question(data):
    """
    Create the analysis question from the actual data.
    This means no dates or battery names are hardcoded —
    it works with any CSV that has the same column structure.
    """

    # Read the actual dates and scenarios from the data
    earliest  = str(data[config.COL_DATETIME].min())
    latest    = str(data[config.COL_DATETIME].max())
    scenarios = sorted(data[config.COL_SCENARIO].unique().tolist())

    # Build the question as a plain sentence
    question = (
        "Please analyse the battery performance data for the period "
        "from " + earliest + " to " + latest + ". "
        "The data has these scenarios: " + ", ".join(scenarios) + ". "
        "Use your tools one by one to: "
        "(1) measure the total revenue gap between historical and perfect, "
        "(2) find the primary and secondary reasons for the gap, and "
        "(3) give two clear recommendations for the battery trader. "
        "Write the full structured analysis report."
    )

    return question


# ============================================================
# STEP 5 — Save the report to a text file
# ============================================================

def save_report(report_text, question_text, output_file="report.txt"):
    """Save the final report to a text file."""

    with open(output_file, "w", encoding="utf-8") as f:
        # Write some header info
        f.write("Report generated : " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
        f.write("Question sent    : " + question_text + "\n")
        f.write("Model used       : " + config.GROQ_MODEL + "\n")
        f.write("\n" + "=" * 70 + "\n\n")
        # Write the actual report
        f.write(report_text)

    print("💾  Report saved to: " + output_file)


# ============================================================
# MAIN — Runs everything in order
# ============================================================

def main():

    # Show a startup banner
    print("")
    print("🔋  Battery Performance Analysis Agent")
    print("    AI Model : " + config.GROQ_MODEL)
    print("")

    # Step 1: Check API key
    check_api_key()

    # Step 2: Check data file
    check_data_file()

    # Step 3: Load data and show summary
    data = load_and_show_data()

    # Step 4: Build the question from the data
    question = build_question(data)
    print("📩  Sending this question to the AI:")
    print('    "' + question + '"')
    print("")

    # Step 5: Run the AI agent
    # show_steps=True means you'll see each tool call printed as it happens
    report = run_agent(question, show_steps=True)

    # Step 6: Print the final report
    print("")
    print("=" * 70)
    print(report)
    print("=" * 70)

    # Step 7: Save the report to a file
    save_report(report, question)


# This line means: only run main() if you run THIS file directly.
# (Prevents it running when another file imports from here)
if __name__ == "__main__":
    main()
