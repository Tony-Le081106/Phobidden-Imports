import json
import os

from dotenv import load_dotenv

from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

def classify_ingredients_to_categories(ingredients_raw: list[str]):
    """
    Classify ingredients into 7 predefined categories.
    Returns booleans + matched ingredients per category.
    """
    schema = {
        "type": "object",
        "properties": {
            "categories": {
                "type": "object",
                "properties": {
                    "rice": {"type": "boolean"},
                    "spices": {"type": "boolean"},
                    "nuts": {"type": "boolean"},
                    "sauces": {"type": "boolean"},
                    "seafood_shellfish_snails": {"type": "boolean"},
                    "meat_products": {"type": "boolean"},
                    "dairy_egg_products": {"type": "boolean"},
                    "Plant materials": {"type": "boolean"},
                    "Seeds / grains / nuts": {"type": "boolean"},
                    "Processed packaged foods": {"type": "boolean"},
                    "Mixed foods": {"type": "boolean"},
                },
                "required": [
                    "rice",
                    "spices",
                    "nuts",
                    "sauces",
                    "seafood_shellfish_snails",
                    "meat_products",
                    "dairy_egg_products",
                    "Plant materials",
                    "Seeds / grains / nuts",
                    "Processed packaged foods",
                    "Mixed foods",
                ],
                "additionalProperties": False,
            },
            "category_matches": {
                "type": "object",
                "properties": {
                    "rice": {"type": "array", "items": {"type": "string"}},
                    "spices": {"type": "array", "items": {"type": "string"}},
                    "nuts": {"type": "array", "items": {"type": "string"}},
                    "sauces": {"type": "array", "items": {"type": "string"}},
                    "seafood_shellfish_snails": {"type": "array", "items": {"type": "string"}},
                    "meat_products": {"type": "array", "items": {"type": "string"}},
                    "dairy_egg_products": {"type": "array", "items": {"type": "string"}},
                    "Plant materials": {"type": "array", "items": {"type": "string"}},
                    "Seeds / grains / nuts": {"type": "array", "items": {"type": "string"}},
                    "Processed packaged foods": {"type": "array", "items": {"type": "string"}},
                    "Mixed foods": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "rice",
                    "spices",
                    "nuts",
                    "sauces",
                    "seafood_shellfish_snails",
                    "meat_products",
                    "dairy_egg_products",
                    "Plant materials",
                    "Seeds / grains / nuts",
                    "Processed packaged foods",
                    "Mixed foods",
                ],
                "additionalProperties": False,
            },
            "attributes": {
                "type": "object",
                "properties": {
                    "processed": {"type": "boolean"},
                    "dried": {"type": "boolean"},
                    "plant_based": {"type": "boolean"},
                    "shelf_stable": {"type": "boolean"},
                    "canned": {"type": "boolean"},
                    "retorted": {"type": "boolean"}
                },
                "required": [
                    "processed",
                    "dried",
                    "plant_based",
                    "shelf_stable",
                    "canned",
                    "retorted"
                ],
                "additionalProperties": False
            },
            "category_reason": {
                "type": "string"
            }
        },
        "required": ["categories", "category_matches", "attributes", "category_reason"],
        "additionalProperties": False
    }

    prompt = f"""
You are a food ingredient categorization assistant.

Your task is to analyze a list of food ingredients and determine:
1. Which biosecurity rule categories the ingredients belong to.
2. Which food attributes apply to the product so that biosecurity rules can be evaluated

11 categories are:
1. rice
2. spices
3. nuts
4. sauces
5. seafood_shellfish_snails
6. meat_products
7. dairy_egg_products
8. Plant materials
9. Seeds / grains / nuts
10. Processed packaged foods
11. Mixed foods

Definitions:
- rice: ingredients made from rice or containing rice such as rice, rice flour, rice paper, rice noodles, rice crackers, rice cakes
- spices: dried or powdered plant ingredients used to season food such as chili, pepper, paprika, turmeric, garlic powder, onion powder, dried herbs, seasoning powder.
- nuts: edible nuts or nut products such as almond, peanut, cashew, walnut, pistachio, hazelnut, peanut powder, crushed nuts.
- sauces: liquid or paste condiments used to flavor food such as soy sauce, fish sauce, oyster sauce, chili sauce, curry paste, dressing, marinade.
- seafood_shellfish_snails: ingredients derived from aquatic animals such as fish, shrimp, prawn, squid, crab, shellfish, anchovy, oyster, tuna, salmon, fish sauce, oyster sauce.
- meat_products: meat or poultry ingredients such as chicken, beef, pork, lamb, bacon, ham, gelatin from animal sources.
- dairy_egg_products: milk, cheese, butter, cream, whey, yogurt, casein, egg, egg yolk, egg white, mayonnaise when clearly egg-based.
- Plant materials: fruits, vegetables, herbs, spices, legumes, mushrooms, cocoa, sugar, plant oils, seaweed only if clearly used as a plant-like ingredient rather than seafood.
- Seeds / grains / nuts: wheat, flour, rice, oats, corn, barley, quinoa, rye, sesame, almond, peanut, cashew, walnut, chia, sunflower seed.
- Processed packaged foods: ingredients that are themselves packaged industrial food products, such as instant noodles, biscuits, cereal bars, chips, candy, canned soup, seasoning sachets, processed snack crumbs.
- Mixed foods: ingredients that are composite prepared foods containing multiple components, such as curry paste, dumpling filling, burger patty, sausage roll filling, salad dressing, sandwich cookie, chocolate spread.

Food attribute detection:
1. processed
2. dried
3. plant_based
4. shelf_stable
5. canned
6. retorted 

- processed: foods that have been manufactured or processed from raw ingredients through cooking, grinding, drying, or industrial preparation such as rice paper, noodles, crackers, seasoning powders, packaged snacks, instant noodles, processed seafood snacks.
- dried: foods that have had moisture removed to preserve them such as dried shrimp, dried chili, dried herbs, dried fish, dried mushrooms.
- plant_based: ingredients derived from plants such as herbs, spices, vegetables, fruits, grains, legumes, seeds, plant oils, garlic, chili, onion.
- shelf_stable: foods that can be stored safely at room temperature without refrigeration such as dried foods, canned foods, sealed snack foods, seasoning powders.
- canned: foods preserved and stored in sealed metal cans such as canned fish, canned vegetables, canned fruit.
- retorted: foods sterilized by heat in a sealed container or pouch to achieve commercial sterility such as retort pouch meals, canned ready meals, sealed retorted food products.

Rules:
- Return all 11 categories and 6 attributes
- For each category, output true if at least one ingredient belongs to it, otherwise false.
- Also return the matched ingredients for each category.
- An ingredient may appear in more than one category only if strongly justified, but avoid over-tagging.
- Use general food knowledge for common ingredients and food terms.
- "Plant materials" includes fruits, vegetables, herbs, legumes, spices, sugar, cocoa, mushrooms, plant oils.
- "Seeds / grains / nuts" includes wheat, flour, oats, rice, corn, barley, quinoa, sesame, almonds, peanuts, cashews, walnuts, etc.
- "Processed packaged foods" includes clearly packaged/industrial items like instant noodles, chips, biscuits, cereal bars, seasoning sachets, canned soup, processed snacks.
- "Mixed foods" should be true only when an ingredient itself is a combined food item, such as curry paste, dumpling filling, sausage roll, burger patty with fillers, chocolate sandwich cookie, mayonnaise-based dressing, or another prepared composite food.
- If no ingredient belongs to a category, return false and an empty list for that category.
- Return valid JSON only.

Ingredients:
{json.dumps(ingredients_raw, ensure_ascii=False)}
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
