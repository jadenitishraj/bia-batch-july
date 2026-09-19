# ---------- FLIGHTS ----------
FLIGHTS = [
    {"id": "SQ-421", "from": "Mumbai", "to": "Singapore", "airline": "Singapore Airlines",
     "depart": "11:45", "arrive": "19:50", "stops": 0, "price_inr": 28500, "red_eye": False},
    {"id": "AI-342", "from": "Mumbai", "to": "Singapore", "airline": "Air India",
     "depart": "23:15", "arrive": "07:20", "stops": 0, "price_inr": 23600, "red_eye": True},
    {"id": "6E-1071", "from": "Mumbai", "to": "Singapore", "airline": "IndiGo",
     "depart": "08:30", "arrive": "16:40", "stops": 0, "price_inr": 21900, "red_eye": False},
    {"id": "MH-199", "from": "Mumbai", "to": "Singapore", "airline": "Malaysia Airlines",
     "depart": "14:20", "arrive": "23:55", "stops": 1, "price_inr": 19400, "red_eye": False},
    {"id": "SQ-423", "from": "Delhi", "to": "Singapore", "airline": "Singapore Airlines",
     "depart": "10:10", "arrive": "19:05", "stops": 0, "price_inr": 31200, "red_eye": False},
    {"id": "6E-1085", "from": "Bangalore", "to": "Singapore", "airline": "IndiGo",
     "depart": "09:05", "arrive": "16:20", "stops": 0, "price_inr": 20800, "red_eye": False},
]

# ---------- HOTELS ----------
HOTELS = [
    {"name": "Hotel Boss", "city": "Singapore", "area": "Lavender",
     "price_per_night_inr": 7200, "rating": 4.0, "style": "budget"},
    {"name": "Village Hotel Bugis", "city": "Singapore", "area": "Bugis",
     "price_per_night_inr": 9800, "rating": 4.3, "style": "mid"},
    {"name": "Hotel G Singapore", "city": "Singapore", "area": "Bencoolen",
     "price_per_night_inr": 8600, "rating": 4.2, "style": "mid"},
    {"name": "Marina Bay Sands", "city": "Singapore", "area": "Marina Bay",
     "price_per_night_inr": 34000, "rating": 4.7, "style": "luxury"},
    {"name": "Hotel Mono", "city": "Singapore", "area": "Chinatown",
     "price_per_night_inr": 10500, "rating": 4.4, "style": "mid"},
    {"name": "The Sultan", "city": "Singapore", "area": "Kampong Glam",
     "price_per_night_inr": 11200, "rating": 4.5, "style": "mid"},
]

# ---------- THINGS TO DO ----------
ACTIVITIES = [
    {"name": "Gardens by the Bay", "city": "Singapore", "interest": "city views", "hours": 3, "area": "Marina Bay"},
    {"name": "Marina Bay Sands SkyPark", "city": "Singapore", "interest": "city views", "hours": 2, "area": "Marina Bay"},
    {"name": "Singapore Flyer", "city": "Singapore", "interest": "city views", "hours": 2, "area": "Marina Bay"},
    {"name": "Chinatown Heritage Centre", "city": "Singapore", "interest": "culture", "hours": 2, "area": "Chinatown"},
    {"name": "Sultan Mosque walk", "city": "Singapore", "interest": "culture", "hours": 2, "area": "Kampong Glam"},
    {"name": "Little India walking tour", "city": "Singapore", "interest": "culture", "hours": 3, "area": "Little India"},
    {"name": "Hawker food trail", "city": "Singapore", "interest": "food", "hours": 3, "area": "Chinatown"},
    {"name": "Sentosa beach day", "city": "Singapore", "interest": "relax", "hours": 5, "area": "Sentosa"},
]

# ---------- FOOD ----------
RESTAURANTS = [
    {"name": "Maxwell Food Centre", "city": "Singapore", "cuisine": "local", "cost_inr": 500, "area": "Chinatown"},
    {"name": "Lau Pa Sat", "city": "Singapore", "cuisine": "local", "cost_inr": 600, "area": "Downtown"},
    {"name": "Komala Vilas", "city": "Singapore", "cuisine": "indian veg", "cost_inr": 700, "area": "Little India"},
    {"name": "Zam Zam", "city": "Singapore", "cuisine": "halal", "cost_inr": 800, "area": "Kampong Glam"},
    {"name": "Newton Food Centre", "city": "Singapore", "cuisine": "seafood", "cost_inr": 1600, "area": "Newton"},
    {"name": "Tiong Bahru Market", "city": "Singapore", "cuisine": "local", "cost_inr": 450, "area": "Tiong Bahru"},
]

# ---------- WEATHER ----------
WEATHER = {
    "singapore": "Hot and humid all year, 26-32 C. Short heavy rain most afternoons. Carry an umbrella.",
    "bangkok":   "Hot, 28-35 C. Heavy rain June to October.",
    "dubai":     "Very hot April to September, 35-45 C. Pleasant November to March.",
}

# ---------- LOCAL TIPS ----------
TIPS = {
    "singapore": "Indian passport holders need a visa. MRT covers the whole city. Buy an EZ-Link card. Tap water is safe. No chewing gum.",
    "bangkok":   "Visa on arrival for Indians. Use BTS Skytrain. Always agree the taxi fare first.",
    "dubai":     "Visa needed in advance. Metro is clean and cheap. Dress modestly in public places.",
}

# ---------- EXCHANGE RATES (1 unit = ? INR) ----------
RATES = {"SGD": 65.0, "USD": 88.0, "THB": 2.5, "AED": 24.0, "INR": 1.0}

print("Data loaded:", len(FLIGHTS), "flights,", len(HOTELS), "hotels,",
      len(ACTIVITIES), "activities,", len(RESTAURANTS), "restaurants.")