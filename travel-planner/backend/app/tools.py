from .data import FLIGHTS, HOTELS, ACTIVITIES, RESTAURANTS, WEATHER, TIPS, RATES
from langchain.tools import tool


@tool
def search_flights(origin: str, destination: str, avoid_red_eye: bool = False,
                   max_price_inr: int = 999999) -> list:
    """Find flights between two cities. Set avoid_red_eye to True to remove overnight flights."""
    # FLIGHTS = await("https://jsonplaceholder.typicode.com/flights")
      # FLIGHTS = select * from flight where time = 12-2-2026
    found = [f for f in FLIGHTS
             if f["from"].lower() == origin.lower()
             and f["to"].lower() == destination.lower()
             and f["price_inr"] <= max_price_inr]
    if avoid_red_eye:
        found = [f for f in found if not f["red_eye"]]
    return sorted(found, key=lambda f: f["price_inr"])


@tool
def search_hotels(city: str, max_price_per_night_inr: int = 999999, style: str = "any") -> list:
    """Find hotels in a city. Style can be budget, mid, luxury or any."""
    found = [h for h in HOTELS
             if h["city"].lower() == city.lower()
             and h["price_per_night_inr"] <= max_price_per_night_inr]
    if style != "any":
        found = [h for h in found if h["style"] == style.lower()]
    return sorted(found, key=lambda h: -h["rating"])


@tool
def search_activities(city: str, interest: str = "any") -> list:
    """Find things to do in a city. Interest can be food, culture, city views, relax or any."""
    found = [a for a in ACTIVITIES if a["city"].lower() == city.lower()]
    if interest != "any":
        found = [a for a in found if interest.lower() in a["interest"]]
    return found


@tool
def search_restaurants(city: str, cuisine: str = "any") -> list:
    """Find places to eat in a city. Cuisine can be local, indian veg, halal, seafood or any."""
    found = [r for r in RESTAURANTS if r["city"].lower() == city.lower()]
    if cuisine != "any":
        found = [r for r in found if cuisine.lower() in r["cuisine"]]
    return sorted(found, key=lambda r: r["cost_inr"])


@tool
def get_weather(city: str) -> str:
    """Get the usual weather for a city, so the plan can allow for rain or heat."""
    return WEATHER.get(city.lower(), "No weather information for this city.")


@tool
def get_travel_tips(city: str) -> str:
    """Get visa, transport and local rules for a city."""
    return TIPS.get(city.lower(), "No tips available for this city.")


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert money between currencies, for example SGD to INR."""
    if from_currency.upper() not in RATES or to_currency.upper() not in RATES:
        return "Currency not supported."
    in_inr = amount * RATES[from_currency.upper()]
    result = in_inr / RATES[to_currency.upper()]
    return f"{amount} {from_currency.upper()} = {round(result, 2)} {to_currency.upper()}"


print("7 tools ready.")