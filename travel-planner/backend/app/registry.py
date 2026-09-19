from .tools import search_flights, search_hotels, search_activities, search_restaurants, get_weather, get_travel_tips, convert_currency
TOOL_REGISTRY = {
    "flight_agent":   [search_flights, convert_currency],
    "hotel_agent":    [search_hotels, convert_currency, get_travel_tips],
    "activity_agent": [search_activities, search_restaurants, get_weather],
    "critic_agent":   [],   # the critic only reads the plan, it does not search
}

# Show the registry as a small table
for agent_name, tools in TOOL_REGISTRY.items():
    tool_names = [t.name for t in tools] or ["(no tools)"]
    print(f"{agent_name:16} -> {', '.join(tool_names)}")