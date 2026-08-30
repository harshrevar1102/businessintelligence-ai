"""Decision rights: which levers each persona is realistically allowed to
act on. Used to filter the Recommendation Engine's output so a Store
Manager doesn't get a strategic pricing recommendation and a CEO doesn't
get a single-store staffing instruction.
"""

DECISION_RIGHTS = {
    "CEO / Executive": ["Promotion", "Pricing", "Peak-hour staffing", "Supplier expediting"],
    "Regional Manager": ["Peak-hour staffing", "Supplier expediting", "Promotion"],
    "Store Manager": ["Peak-hour staffing", "Supplier expediting"],
}


def can_act_on(persona, lever):
    return lever in DECISION_RIGHTS.get(persona, [])


def filter_action_plans(persona, action_plans):
    return [p for p in action_plans if can_act_on(persona, p.lever)]
