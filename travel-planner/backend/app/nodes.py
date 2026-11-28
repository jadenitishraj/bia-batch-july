from .agents import ask, manager_agent, flight_agent, hotel_agent, activity_agent, critic_agent
from .event_log import log_event, observed


@observed('node')
def manager_node(state):
    """Read the request. Write down the requirements. Decide who should work."""
    requirements = ask(manager_agent, f"""
Read this travel request and list what you understood.

REQUEST: {state['request']}

List these lines only:
FROM, TO, DAYS, TRAVELLERS, BUDGET, INTERESTS, HARD RULES, MISSING INFO
""")

    choice = ask(manager_agent, f"""
Here are the requirements:
{requirements}

Which specialists are needed? Choose from: flight_agent, hotel_agent, activity_agent.
Reply with the names separated by commas and nothing else.
""")

    # Keep only names we actually have. This protects us if the model adds something extra.
    valid = ["flight_agent", "hotel_agent", "activity_agent"]
    workers = [name for name in valid if name in choice.lower()]
    fallback = not workers
    if fallback:
        workers = valid          # if unsure, use everyone

    log_event('manager.routing', selected_workers=workers,
              decision='fallback_all' if fallback else 'selected_specialists')
    return {"requirements": requirements, "chosen_workers": workers}


@observed('node')
def flight_node(state):
    """The flight agent works on its part."""
    report = ask(flight_agent, f"Find flights for this trip.\n\n{state['requirements']}")
    return {"flight_report": report}


@observed('node')
def hotel_node(state):
    """The hotel agent works on its part."""
    report = ask(hotel_agent, f"Find hotels for this trip.\n\n{state['requirements']}")
    return {"hotel_report": report}


@observed('node')
def activity_node(state):
    """The activity agent works on its part."""
    report = ask(activity_agent, f"Plan the days for this trip.\n\n{state['requirements']}")
    return {"activity_report": report}


@observed('node')
def synthesis_node(state):
    """The manager joins the three reports into one travel plan."""
    draft = ask(manager_agent, f"""
Write the first version of the travel plan using ONLY the reports below.

REQUIREMENTS:
{state['requirements']}

FLIGHT REPORT:
{state.get('flight_report', 'not requested')}

HOTEL REPORT:
{state.get('hotel_report', 'not requested')}

ACTIVITY REPORT:
{state.get('activity_report', 'not requested')}

Use these headings:
CHOSEN FLIGHT, CHOSEN HOTEL, DAY BY DAY PLAN, TOTAL COST, WHY THESE CHOICES, ASSUMPTIONS
""")
    return {"draft_plan": draft}


@observed('node')
def critic_node(state):
    """The critic looks for problems. It does not fix them."""
    issues = ask(critic_agent, f"""
Review this plan against the requirements.

REQUIREMENTS:
{state['requirements']}

PLAN:
{state['draft_plan']}
""")
    return {"critique": issues}


@observed('node')
def revision_node(state):
    """The manager fixes only what the critic listed. Everything else stays as it was."""
    if "NO ISSUES FOUND" in state["critique"].upper():
        log_event('revision.decision', decision='approved_without_changes')
        return {"final_plan": state["draft_plan"]}

    log_event('revision.decision', decision='apply_critic_fixes')
    fixed = ask(manager_agent, f"""
Fix ONLY the problems listed below. Do not rewrite the parts that are fine.

PLAN:
{state['draft_plan']}

PROBLEMS TO FIX:
{state['critique']}

Return the full corrected plan, then a short section called WHAT CHANGED.
""")
    return {"final_plan": fixed}


print("7 nodes ready.")
