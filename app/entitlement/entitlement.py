"""Simulated role-based entitlement.

There is no authentication in this prototype. Instead, selecting a
persona pins the user to whatever cities/stores that persona is allowed
to see, and every analytical function below filters data before any
calculation happens - not just at the display layer.
"""

from app.config.settings import PERSONA_ENTITLEMENTS, CITIES, STORES


def get_entitlement(persona):
    return PERSONA_ENTITLEMENTS.get(persona, {"cities": None, "store": None})


def allowed_cities(persona):
    ent = get_entitlement(persona)
    if ent["cities"] is None:
        return CITIES
    return ent["cities"]


def allowed_locations(persona):
    """Returns the list of selectable location labels for the location dropdown."""
    ent = get_entitlement(persona)
    if ent["store"] is not None:
        city = ent["cities"][0]
        return [f"{city} - {ent['store']}"]

    cities = allowed_cities(persona)
    options = ["All India"] if ent["cities"] is None else []
    for city in cities:
        options.append(city)
        for store in STORES.get(city, []):
            options.append(f"{city} - {store}")
    return options


def parse_location(location_label):
    """Splits a location dropdown label into (city, store), either of which may be None."""
    if location_label == "All India":
        return None, None
    if " - " in location_label:
        city, store = location_label.split(" - ", 1)
        return city, store
    return location_label, None


def filter_dataframe(df, persona, location_label, city_col="city", store_col="store"):
    """Applies persona entitlement AND the user's location selection to a dataframe."""
    ent = get_entitlement(persona)
    out = df

    if ent["cities"] is not None:
        out = out[out[city_col].isin(ent["cities"])]
    if ent["store"] is not None:
        out = out[out[store_col] == ent["store"]]

    city, store = parse_location(location_label)
    if city is not None:
        out = out[out[city_col] == city]
    if store is not None and store_col in out.columns:
        out = out[out[store_col] == store]

    return out


def enforce_default_location(persona, requested_location):
    """Makes sure the requested location is actually within this persona's entitlement."""
    valid = allowed_locations(persona)
    if requested_location in valid:
        return requested_location
    return valid[0]
