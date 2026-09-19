from typing import TypedDict, List


class TravelState(TypedDict):
    request: str            # what the user typed
    requirements: str       # what the manager understood
    chosen_workers: List[str]  # who the manager picked
    flight_report: str      # written by the flight agent
    hotel_report: str       # written by the hotel agent
    activity_report: str    # written by the activity agent
    draft_plan: str         # the manager's first attempt
    critique: str           # the critic's list of problems
    final_plan: str         # the fixed plan


print("State defined.")