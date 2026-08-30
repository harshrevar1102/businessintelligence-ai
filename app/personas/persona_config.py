"""Decision rights: which levers each persona is realistically allowed to
act on. Used to filter the Recommendation Engine's output so a Store
Manager doesn't get a strategic pricing recommendation and a CEO doesn't
get a single-store staffing instruction.
"""

DECISION_RIGHTS = {
    "CEO / Executive": [
        "Campaign reactivation",     # Promotion Ended driver
        "Promotional pricing",        # Pricing / Product Mix driver
        "Peak-hour staffing",         # Wait Time / Staffing driver
        "Supplier expediting"         # Inventory Stockout driver
    ],
    "Regional Manager": ["Peak-hour staffing", "Supplier expediting", "Campaign reactivation"],
    "Store Manager": ["Peak-hour staffing", "Supplier expediting"],
}


def can_act_on(persona, lever):
    return lever in DECISION_RIGHTS.get(persona, [])


def filter_action_plans(persona, action_plans):
    return [p for p in action_plans if can_act_on(persona, p.lever)]
