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
                return jsonify(result)

            # if barcode exists but OFF has no product, fall back to Gemini
            gemini_result = analyze_with_gemini(image_bytes, mime_type)
            gemini_result["barcode"] = barcode
            gemini_result["source"] = "gemini_fallback_after_barcode"
            return jsonify(gemini_result)

        # 2) No barcode found -> Gemini
        result = analyze_with_gemini(image_bytes, mime_type)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)