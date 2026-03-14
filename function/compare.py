import json

VERDICT_PRIORITY = {
    "DONT_BRING": 3,
    "DECLARE_IT": 2,
    "BRING_IT": 1
}

with open("reference.json", "r", encoding="utf-8") as f:
    reference_rules = json.load(f)

rules_map = {rule["item"]: rule for rule in reference_rules}


def check_conditions(rule_conditions, result):

    attributes = result.get("attributes", {})

    matched = []
    failed = []
    missing = []

    for key, value in rule_conditions.items():

        # max_* conditions
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
            ingredients = result.get("ingredients_raw", [])

            if not ingredients:
                missing.append(key)
            else:
                if any(i in value for i in ingredients):
                    failed.append(key)
                else:
                    matched.append(key)

        # standard attribute
        else:
            if key not in attributes:
                missing.append(key)
            elif attributes[key] == value:
                matched.append(key)
            else:
                failed.append(key)

    return matched, failed, missing


def compare_rules(result):

    categories = result.get("categories", {})

    final_verdict = "BRING_IT"
    matched_rules = []
    reasons = []
    reports = []

    for category, is_true in categories.items():

        # skip categories that are not rules
        if not is_true or category not in rules_map:
            continue

        rule = rules_map[category]
        conditions = rule.get("conditions", {})

        if conditions:
            matched, failed, missing = check_conditions(conditions, result)
        else:
            matched, failed, missing = [], [], []

        reports.append({
            "item": category,
            "matched_conditions": matched,
            "failed_conditions": failed,
            "missing_conditions": missing
        })

        matched_rules.append(category)
        reasons.append(rule["reason"])

        verdict = rule["verdict"]

        if VERDICT_PRIORITY[verdict] > VERDICT_PRIORITY[final_verdict]:
            final_verdict = verdict

    return {
        "verdict": final_verdict,
        "matched_rules": matched_rules,
        "reasons": reasons,
        "condition_reports": reports
    }