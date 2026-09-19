from .state import TravelState
from .nodes import manager_node, flight_node, hotel_node, activity_node, synthesis_node, critic_node, revision_node
from langgraph.graph import StateGraph, START, END

graph = StateGraph(TravelState)

# Add every step
graph.add_node("manager", manager_node)
graph.add_node("flight_agent", flight_node)
graph.add_node("hotel_agent", hotel_node)
graph.add_node("activity_agent", activity_node)
graph.add_node("synthesis", synthesis_node)
graph.add_node("critic", critic_node)
graph.add_node("revision", revision_node)

# Start at the manager
graph.add_edge(START, "manager")

# The manager's list of workers decides who runs. All of them start together.
graph.add_conditional_edges(
    "manager",
    lambda state: state["chosen_workers"],
    ["flight_agent", "hotel_agent", "activity_agent"],
)

# Whoever ran, they all meet at synthesis
graph.add_edge("flight_agent", "synthesis")
graph.add_edge("hotel_agent", "synthesis")
graph.add_edge("activity_agent", "synthesis")

# Then the quality loop
graph.add_edge("synthesis", "critic")
graph.add_edge("critic", "revision")
graph.add_edge("revision", END)

travel_planner = graph.compile()
print("Graph built.")