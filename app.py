import io
import json
import os
import re

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from PIL import Image
from pyzbar.pyzbar import decode
import requests

from google import genai
from google.genai import types

from compare import compare_rules

load_dotenv()

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# ----------------------------
# Helpers
# ----------------------------

def detect_barcode(image_bytes: bytes):
    """
    Try to decode barcode from uploaded image.
    Returns barcode string if found, else None.
    """
    image = Image.open(io.BytesIO(image_bytes))
    decoded_objects = decode(image)

    if not decoded_objects:
        return None

    # just take the first barcode found
    return decoded_objects[0].data.decode("utf-8")


def get_product_by_barcode(barcode: str):
    """
    Query Open Food Facts using barcode.
    OFF API v2 barcode endpoint:
    https://world.openfoodfacts.net/api/v2/product/{barcode}
    """
    url = f"https://world.openfoodfacts.net/api/v2/product/{barcode}"
    res = requests.get(url, timeout=15)

    if not res.ok:
        raise Exception("Open Food Facts lookup failed")

    return res.json()


def parse_ingredients_from_off(product_data: dict):
    """
    Extract ingredients_raw from Open Food Facts product data.
    Prefer ingredients_text if present.
    """
    product = product_data.get("product", {})

    ingredients_raw = []

    # 1) best easy source
    ingredients_text = product.get("ingredients_text")
    if ingredients_text:
        parts = re.split(r",|;|\.", ingredients_text)
        ingredients_raw = [p.strip() for p in parts if p.strip()]
        return ingredients_raw

    # 2) fallback: structured ingredients
    structured_ingredients = product.get("ingredients", [])
    for item in structured_ingredients:
        text = item.get("text")
        if text:
            ingredients_raw.append(text.strip())

    return ingredients_raw


def build_off_response(barcode: str, off_data: dict):
    """
    Convert OFF response into your app JSON shape.
    """
    product = off_data.get("product", {})
    ingredients_raw = parse_ingredients_from_off(off_data)

    return {
        "product_name": product.get("product_name"),
        "barcode": barcode,
        "input_type": ["image", "barcode"],
        "is_commercial_packaged": True,
        "is_homemade": False,
        "packaging_state": "unknown",
        "ingredients_raw": ingredients_raw,
        "source": "open_food_facts"
    }


def analyze_with_gemini(image_bytes: bytes, mime_type: str):
    """
    Send image to Gemini and ask for JSON only.
    """
    schema = {
        "type": "object",
        "properties": {
            "product_name": {
                "type": ["string", "null"],
                "description": "Product name if identifiable."
            },
            "barcode": {
                "type": ["string", "null"],
                "description": "Barcode if visible, else null."
            },
            "input_type": {
                "type": "array",
                "items": {"type": "string"}
            },
            "is_commercial_packaged": {
                "type": "boolean"
            },
            "is_homemade": {
                "type": "boolean"
            },
            "packaging_state": {
                "type": "string",
                "description": "One of sealed, open, unknown."
            },
            "ingredients_raw": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Raw visible or strongly inferred ingredients."
            }
        },
        "required": [
            "product_name",
            "barcode",
            "input_type",
            "is_commercial_packaged",
            "is_homemade",
            "packaging_state",
            "ingredients_raw"
        ]
    }

    prompt = """
You are a food image extraction assistant.

Look at the uploaded food image and return JSON only.

Rules:
- Do NOT make biosecurity decisions.
- Extract only product facts.
- If you are unsure, still return valid JSON.
- ingredients_raw should contain visible or strongly supported ingredients only.
- If you cannot identify ingredients, return an empty array.
- packaging_state must be one of: sealed, open, unknown.
- barcode should be null if not visible.
- input_type should be ["image"].

Output fields:
- product_name
- barcode
- input_type
- is_commercial_packaged
- is_homemade
- packaging_state
- ingredients_raw
"""

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            ),
            prompt
        ],
        config={
            "response_mime_type": "application/json",
            "response_json_schema": schema,
        }
    )

    data = json.loads(response.text)
    data["source"] = "gemini"
    return data

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


def allowed_file_mime(mime_type: str):
    return mime_type in {"image/jpeg", "image/png", "image/webp"}



# ----------------------------
# Routes
# ----------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    mime_type = file.mimetype
    if not allowed_file_mime(mime_type):
        return jsonify({"error": "Only JPG, PNG, WEBP supported"}), 400

    image_bytes = file.read()

    try:
        # 1) Try barcode route first
        barcode = detect_barcode(image_bytes)

        if barcode:
            off_data = get_product_by_barcode(barcode)

            # if OFF found product, use OFF result
            if off_data.get("product"):
                result = build_off_response(barcode, off_data)
                classification = classify_ingredients_to_categories(
                    result.get("ingredients_raw", [])
                )
                result.update(classification)
                return jsonify(result)

            # if barcode exists but OFF has no product, fall back to Gemini
            gemini_result = analyze_with_gemini(image_bytes, mime_type)
            gemini_result["barcode"] = barcode
            gemini_result["source"] = "gemini_fallback_after_barcode"

            classification = classify_ingredients_to_categories(
                gemini_result.get("ingredients_raw", [])
            )
            gemini_result.update(classification)
            biosecurity_result = compare_rules(gemini_result)
            gemini_result["biosecurity_result"] = biosecurity_result

            return jsonify(gemini_result)

        # 2) No barcode found -> Gemini
        result = analyze_with_gemini(image_bytes, mime_type)

        classification = classify_ingredients_to_categories(
            result.get("ingredients_raw", [])
        )
        result.update(classification)
        biosecurity_result = compare_rules(result)
        result["biosecurity_result"] = biosecurity_result

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)