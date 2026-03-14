import json
import os

VERDICT_PRIORITY = {
    "DONT_BRING": 3,
    "DECLARE_IT": 2,
    "BRING_IT": 1
}

# load rule
RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "reference.json")

with open(RULES_PATH, encoding="utf-8") as _f:
    _RULES = json.load(_f)

RULES_MAP  = {rule["item"]: rule for rule in _RULES}
RULE_KEYS  = list(RULES_MAP.keys())


def check_conditions(rule_conditions: dict, compare_input: dict):
    attributes = compare_input.get("attributes", {})
    matched = []
    failed  = []
    missing = []

    for key, value in rule_conditions.items():

        # max_* → numeric upper bound
        if key.startswith("max_"):
            attr = key.replace("max_", "")
            if attr not in attributes:
                missing.append(key)
            elif attributes[attr] <= value:
                matched.append(key)
            else:
                failed.append(key)

        # exclusion list
        elif key == "are_not":
            ingredients = compare_input.get("ingredients_raw", [])
            if not ingredients:
                missing.append(key)
            elif any(i.lower() in [v.lower() for v in value] for i in ingredients):
                failed.append(key)
            else:
                matched.append(key)

        # standard boolean / value check
        else:
            if key not in attributes:
                missing.append(key)
            elif attributes[key] == value:
                matched.append(key)
            else:
                failed.append(key)

    return matched, failed, missing


def compare_rules(compare_input: dict) -> dict:
    # return
    #   overall_verdict:
    #   matched_rules:
    #   reasons:      
    #   condition_reports:
    #   rules_applied:   

    categories = compare_input.get("categories", {})

    final_verdict = "BRING_IT"
    matched_rules = []
    reasons       = []
    reports       = []

    for rule_key, is_active in categories.items():
        if not is_active or rule_key not in RULES_MAP:
            continue

        rule       = RULES_MAP[rule_key]
        conditions = rule.get("conditions", {})

        if conditions:
            matched, failed, missing = check_conditions(conditions, compare_input)
        else:
            matched, failed, missing = [], [], []

        reports.append({
            "item":               rule_key,
            "matched_conditions": matched,
            "failed_conditions":  failed,
            "missing_conditions": missing,
        })

        matched_rules.append(rule_key)
        reasons.append(rule["reason"])

        verdict = rule["verdict"]
        if VERDICT_PRIORITY[verdict] > VERDICT_PRIORITY[final_verdict]:
            final_verdict = verdict

    return {
        "overall_verdict":   final_verdict,
        "matched_rules":     matched_rules,
        "reasons":           reasons,
        "condition_reports": reports,
        "rules_applied":     [RULES_MAP[k] for k in matched_rules if k in RULES_MAP],
    }