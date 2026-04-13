# ============================================================
# agent/agent.py — The AI brain that calls tools and writes the report
#
# HOW THIS FILE WORKS (simple explanation):
#
#   Imagine a conversation between you and a very smart assistant:
#
#   YOU:       "Analyse this battery's performance."
#   ASSISTANT: "Let me check the revenue first."
#              [calls compute_revenue_summary tool]
#              "OK, the gap is $5,320. Let me check high prices next..."
#              [calls identify_high_price_intervals tool]
#              "The battery missed 15 of the top 20 price spikes."
#              [calls more tools...]
#              "I have enough info now. Here is my report."
#
#   That back-and-forth loop is what this file manages.
#   The AI (Groq) decides WHAT to do next.
#   Python runs the tool and sends the result back to the AI.
# ============================================================

import json        # used to convert Python dicts to text (JSON)
from groq import Groq  # the Groq AI library

import config
from agent.tools import run_tool   # the function that runs our tools


# ============================================================
# PART 1 — TELL THE AI WHAT TOOLS EXIST
#
# We describe each tool to the AI in a special format.
# This lets the AI know: "I can call THIS function with THESE arguments."
# ============================================================

TOOL_DESCRIPTIONS = [
    {
        "type": "function",
        "function": {
            "name": "compute_revenue_summary",
            "description": (
                "CALL THIS FIRST. "
                "Adds up total revenue for both scenarios and returns the dollar gap."
            ),
            "parameters": {
                "type": "object",
                "properties": {},     # no arguments needed
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "identify_high_price_intervals",
            "description": (
                "CALL THIS SECOND. "
                "Finds the top N most expensive intervals and checks if the battery "
                "was discharging during those moments. Pass top_n=20."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "How many top-price intervals to look at. Use 20.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_dispatch",
            "description": (
                "CALL THIS THIRD. "
                "Compares charge and discharge totals between scenarios. "
                "Counts how many times the historical battery was idle when "
                "the perfect battery was active."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_state_of_charge",
            "description": (
                "CALL THIS FOURTH. "
                "Shows the battery charge level (SOC) over the day. "
                "SOC=0 means empty, SOC=1 means full. "
                "Use scenario='both' to compare both."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "string",
                        "enum": ["historical", "perfect", "both"],
                        "description": "Which scenario to check. Use 'both'.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_missed_opportunities",
            "description": (
                "CALL THIS FIFTH. "
                "Finds intervals where the perfect battery earned money "
                "but the historical battery did nothing. "
                "Shows total revenue missed and the 10 worst moments."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "price_threshold": {
                        "type": "number",
                        "description": (
                            "Minimum price to consider ($/MWh). "
                            "Leave empty to auto-detect the 75th percentile."
                        ),
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_efficiency_ratio",
            "description": (
                "CALL THIS SIXTH. "
                "Calculates revenue per MWh for each scenario. "
                "Higher = battery was active at better-priced times."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_revenue_by_period",
            "description": (
                "CALL THIS SEVENTH. "
                "Breaks revenue into time-of-day buckets (off_peak, shoulder, peak). "
                "Shows which part of the day caused the biggest gap. "
                "Use period_type='time_of_day'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "period_type": {
                        "type": "string",
                        "enum": ["hour", "time_of_day"],
                        "description": "Use 'time_of_day' for off_peak / shoulder / peak buckets.",
                    }
                },
                "required": [],
            },
        },
    },
]


# ============================================================
# PART 2 — INSTRUCTIONS FOR THE AI (called the "system prompt")
#
# This is sent to the AI at the start and tells it:
#   - What its job is
#   - What order to call the tools
#   - What the final report must look like
# ============================================================

SYSTEM_INSTRUCTIONS = """
You are a battery market analyst. Your job is to analyse battery performance
data and write a clear report for a battery trader.

You have 7 analysis tools. Call them in this exact order:

  Step 1  →  compute_revenue_summary          (total revenue + gap)
  Step 2  →  identify_high_price_intervals    (top_n=20)
  Step 3  →  compare_dispatch                 (charge/discharge differences)
  Step 4  →  analyze_state_of_charge          (scenario="both")
  Step 5  →  find_missed_opportunities        (highest-cost missed events)
  Step 6  →  compute_efficiency_ratio         (revenue per MWh)
  Step 7  →  compute_revenue_by_period        (period_type="time_of_day")

After all 7 tools are done, write your final report.

RULES:
  - Every number in the report must come from a tool result.
  - Do NOT make up numbers.
  - Recommendations must be specific — no vague advice.

REPORT FORMAT (use this exactly):

=== BATTERY PERFORMANCE ANALYSIS REPORT ===
Period: [dates from tool]

SECTION 1: PERFORMANCE GAP
  Historical Revenue : $X,XXX.XX
  Perfect Revenue    : $X,XXX.XX
  Gap                : $X,XXX.XX  (XX.X% of perfect revenue)

SECTION 2: PRIMARY DRIVER
  Title       : [short title]
  Explanation : [2-3 sentences — what caused the gap?]
  Evidence    :
    - [specific number from a tool]
    - [another specific number from a tool]

SECTION 3: SECONDARY DRIVER
  Title       : [short title]
  Explanation : [2-3 sentences]
  Evidence    :
    - [specific number from a tool]

SECTION 4: RECOMMENDATIONS
  Recommendation 1:
    Action    : [what to do]
    Reason    : [why — use tool evidence]
    Benefit   : [expected improvement]
    Tradeoff  : [one honest downside]

  Recommendation 2:
    Action    : [what to do]
    Reason    : [why — use tool evidence]
    Benefit   : [expected improvement]
    Tradeoff  : [one honest downside]

SECTION 5: SUMMARY
  [3-4 sentences for a battery trader to quickly understand the findings]
""".strip()


# ============================================================
# PART 3 — THE MAIN AGENT LOOP
#
# This function runs the full back-and-forth between the AI and tools.
# It keeps going until the AI writes its final report.
# ============================================================

def run_agent(user_question, show_steps=True):
    """
    Run the AI agent from start to final report.

    Parameters:
        user_question:  the analysis request text
        show_steps:     if True, print each tool call as it happens

    Returns:
        The final report text (a string)
    """

    # Connect to Groq using our API key
    client = Groq(api_key=config.GROQ_API_KEY)

    # Start the conversation with the system instructions and the user question
    # This is like the "chat history" — we keep adding to it as we go
    conversation = [
        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
        {"role": "user",   "content": user_question},
    ]

    round_number = 0   # counts how many rounds we've done

    # Keep looping until the AI is done
    while round_number < config.MAX_ROUNDS:

        round_number = round_number + 1   # increment round counter

        if show_steps:
            print("\n" + "-" * 50)
            print("  Agent Round " + str(round_number))
            print("-" * 50)

        # Send the current conversation to the AI and get a response
        response = client.chat.completions.create(
            model       = config.GROQ_MODEL,
            messages    = conversation,
            tools       = TOOL_DESCRIPTIONS,
            tool_choice = "auto",    # AI decides: call a tool OR write the report
            temperature = 0.1,       # low = consistent, analytical answers
            max_tokens  = 4096,
        )

        # Get the AI's reply and why it stopped
        ai_reply      = response.choices[0].message
        stop_reason   = response.choices[0].finish_reason

        # Add the AI's reply to our conversation history
        conversation.append(ai_reply.model_dump(exclude_none=True))

        # ── CASE A: The AI is done — it wrote the final report ─────────────
        if stop_reason == "stop":
            if show_steps:
                print("\n✅  Agent done — final report ready!\n")
            return ai_reply.content or ""

        # ── CASE B: The AI wants to call a tool ────────────────────────────
        if stop_reason == "tool_calls" and ai_reply.tool_calls:

            # The AI might request multiple tools at once, so we loop
            for tool_call in ai_reply.tool_calls:

                tool_name = tool_call.function.name   # which tool to run

                # Parse the arguments the AI wants to pass to the tool
                try:
                    tool_arguments = json.loads(tool_call.function.arguments or "{}")
                except:
                    tool_arguments = {}   # if parsing fails, use no arguments

                if show_steps:
                    print("\n🔧  Tool called: " + tool_name)
                    if tool_arguments:
                        print("    Arguments : " + str(tool_arguments))

                # Run the actual Python tool function
                tool_result = run_tool(tool_name, tool_arguments)

                if show_steps:
                    # Show a short preview of the result
                    result_text = json.dumps(tool_result, indent=2)
                    print("    Result    :\n" + result_text[:400])
                    if len(result_text) > 400:
                        print("    ...(more data not shown)...")

                # Add the tool result to the conversation
                # so the AI can use it in the next round
                conversation.append({
                    "role":         "tool",
                    "tool_call_id": tool_call.id,
                    "name":         tool_name,
                    "content":      json.dumps(tool_result),
                })

        else:
            # Something unexpected happened — return whatever the AI said
            if show_steps:
                print("⚠️  Unexpected stop: " + str(stop_reason))
            return ai_reply.content or ""

    # If we hit the round limit, return a warning
    return (
        "⚠️  The agent ran too many rounds without finishing.\n"
        "    Check the tool results printed above for partial analysis."
    )
