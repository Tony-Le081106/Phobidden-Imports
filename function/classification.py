import json
import os

from dotenv import load_dotenv

from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# load rule
RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "reference.json")

with open(RULES_PATH, encoding="utf-8") as _f:
    _RULES = json.load(_f)

RULES_MAP  = {rule["item"]: rule for rule in _RULES}
RULE_KEYS  = list(RULES_MAP.keys())

def classify_for_rules(base_data: dict) -> dict:
    # classify to match rule
    # output
    #   categories:
    #   category_matches:
    #   attributes
    ingredients_raw = base_data.get("ingredients_raw", [])
    product_name    = base_data.get("product_name") or "Unknown"
    is_commercial   = base_data.get("is_commercial_packaged", False)
    packaging_state = base_data.get("packaging_state", "unknown")
    is_homemade     = base_data.get("is_homemade", False)


    categories_props = {k: {"type": "boolean"} for k in RULE_KEYS}
    matches_props    = {k: {"type": "array", "items": {"type": "string"}} for k in RULE_KEYS}

    schema = {
        "type": "object",
        "properties": {
            "categories": {
                "type": "object",
                "properties": categories_props,
                "required": RULE_KEYS,
                "additionalProperties": False,
            },
            "category_matches": {
                "type": "object",
                "properties": matches_props,
                "required": RULE_KEYS,
                "additionalProperties": False,
            },
            "attributes": {
                "type": "object",
                "properties": {
                    "commercial_packaging":   {"type": "boolean"},
                    "shelf_stable":           {"type": "boolean"},
                    "fully_cooked":           {"type": "boolean"},
                    "contains_meat":          {"type": "boolean"},
                    "personal_use":           {"type": "boolean"},
                    "plant_based":            {"type": "boolean"},
                    "plant_origin_only":      {"type": "boolean"},
                    "processed":              {"type": "boolean"},
                    "dried":                  {"type": "boolean"},
                    "canned":                 {"type": "boolean"},
                    "retorted":               {"type": "boolean"},
                    "roasted":                {"type": "boolean"},
                    "instant_use":            {"type": "boolean"},
                    "clean_packaging":        {"type": "boolean"},
                    "human_consumption":      {"type": "boolean"},
                    "commercially_milled":    {"type": "boolean"},
                    "botanical_label":        {"type": "boolean"},
                    "fmd_free_country":       {"type": "boolean"},
                    "certificate_required":   {"type": "boolean"},
                    "import_permit_required": {"type": "boolean"},
                    "personal_use_infant":    {"type": "boolean"},
                },
                "additionalProperties": False,
            },
        },
        "required": ["categories", "category_matches", "attributes"],
        "additionalProperties": False,
    }

    prompt = f"""
You are an Australian biosecurity ingredient classifier.

Product: "{product_name}"
Commercially packaged: {is_commercial}
Packaging state: {packaging_state}
Homemade: {is_homemade}
Ingredients: {json.dumps(ingredients_raw, ensure_ascii=False)}

PART 1 — categories + category_matches

Map the ingredients to these rule item keys (use ONLY keys from this list):
{json.dumps(RULE_KEYS, indent=2)}

Set true if any ingredient belongs to that rule category; false otherwise.
In category_matches, list the specific triggering ingredients for each true key.
An ingredient may appear under multiple keys only if genuinely justified.

Mapping guidance:
- meat_products            → meat, poultry, pork, beef, lamb, gelatin, lard, tallow
- dairy_products           → milk, cheese, butter, cream, whey, yogurt, casein, condensed milk
- whole_eggs               → whole eggs only (not processed egg products)
- seafood_shellfish_snails → shrimp, prawn, crab, shellfish, scallop, oyster, squid, octopus, snail
- fish_non_salmonid        → fish other than salmon/trout (tuna, anchovy, tilapia, cod, sardine)
- fish_salmon_trout        → salmon or trout specifically
- prawns_products          → prawn or shrimp as primary product
- nuts                     → almonds, peanuts, cashews, walnuts, pistachios, hazelnuts, macadamia
- wheat                    → wheat flour, whole wheat (NOT rice flour or other grains)
- rice                     → cooked/processed rice, rice flour, rice noodles
- raw_rice                 → uncooked raw rice grains only
- noodles_pasta            → noodles, pasta, instant noodles, vermicelli
- biscuits_bread_cakes_pastries → biscuits, crackers, cakes, pastries, bread products
- chocolate_confectionery  → chocolate, candy, sweets, confectionery
- spices                   → spices generally (pepper is separate; cumin/coriander/fennel/dried chillies/capsicum are restricted separately)
- pepper                   → black pepper, white pepper, peppercorns
- dried_herbs_herbal_teas  → dried herbs, loose herbal teas, dried plant leaves for tea
- black_green_tea          → black, green, or oolong tea leaves
- herbal_tea               → herbal infusions (chamomile, peppermint, etc.)
- sauces                   → sauces, pastes, curry paste, chili sauce, soy sauce, fish sauce, oyster sauce
- preserved_fruit_vegetables → canned/pickled fruit or vegetables, jam, dried fruit
- vegetable_oils           → cooking oils, vegetable oil, palm oil, coconut oil, sesame oil
- honey_products           → honey or honey-derived products
- maple_syrup              → maple syrup only
- juice_soft_drink         → fruit juice, soft drink, cordial, energy drink
- roasted_coffee           → roasted coffee beans, ground coffee, instant coffee
- green_coffee             → unroasted / green coffee beans
- kopi_luwak_cviet_coffee  → kopi luwak / civet coffee specifically
- instant_beverage_sachets → instant coffee sachets, instant milk tea, 3-in-1 drinks
- vitamins_supplements     → vitamin tablets, mineral supplements, herbal capsules
- infant_formula           → baby formula, infant formula powder
- breast_milk              → human breast milk
- pet_food                 → pet food, animal feed
- food_from_plane_or_ship  → food taken from aircraft or ship catering


PART 2 — attributes

Infer from product context:

- commercial_packaging:   true if is_commercial_packaged AND packaging is sealed/unknown
- clean_packaging:        same as commercial_packaging
- shelf_stable:           true if clearly shelf-stable (sealed, non-perishable, dried, canned)
- fully_cooked:           true if clearly a cooked/baked/processed food
- contains_meat:          true if any meat ingredient present
- personal_use:           always true (travellers carry personal quantities)
- human_consumption:      true unless clearly pet/animal feed
- plant_based:            true if main ingredients are plant-derived
- plant_origin_only:      true if ALL ingredients are 100% plant origin
- processed:              true if not raw/whole (e.g. rice flour = processed; raw rice = not)
- dried:                  true if product is dried/dehydrated
- canned:                 true if product is in a sealed can
- retorted:               true if canned at high temperature (assume true when canned)
- roasted:                true if coffee or nuts are clearly roasted
- instant_use:            true for instant beverages or instant noodles
- commercially_milled:    true for milled flour / commercially processed wheat
- botanical_label:        false unless explicitly stated on label
- fmd_free_country:       false (conservative — cannot verify country of origin)
- certificate_required:   false by default
- import_permit_required: false by default
- personal_use_infant:    false unless product is specifically for infant use

Return valid JSON only.
"""

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": schema,
        },
    )

    return json.loads(response.text)
