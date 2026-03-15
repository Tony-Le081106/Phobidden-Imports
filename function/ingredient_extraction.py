import io
import json
import os
import re


from dotenv import load_dotenv
from PIL import Image
from pyzbar.pyzbar import decode
import requests

from google import genai
from google.genai import types


load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


def detect_barcode(image_bytes: bytes):
    # Use pyzbar to detect barcodes in the image
    image = Image.open(io.BytesIO(image_bytes))
    decoded_objects = decode(image)
    if not decoded_objects:
        return None
    return decoded_objects[0].data.decode("utf-8")


def get_product_by_barcode(barcode: str):
    # Query Open Food Facts API for product information based on the barcode
    url = f"https://world.openfoodfacts.net/api/v2/product/{barcode}"
    res = requests.get(url, timeout=15)
    if not res.ok:
        raise Exception("Open Food Facts lookup failed")
    return res.json()


def parse_ingredients_from_off(product_data: dict):
    # Extract ingredients from Open Food Facts product data
    product = product_data.get("product", {})
    ingredients_text = product.get("ingredients_text")
    if ingredients_text:
        parts = re.split(r",|;|\.", ingredients_text)
        return [p.strip() for p in parts if p.strip()]
    structured = product.get("ingredients", [])
    return [item.get("text", "").strip() for item in structured if item.get("text")]


def build_off_base(barcode: str, off_data: dict) -> dict:
    # Build base data structure from Open Food Facts response
    product = off_data.get("product", {})
    return {
        "product_name":           product.get("product_name"),
        "barcode":                barcode,
        "input_type":             ["barcode"],
        "is_commercial_packaged": True,
        "is_homemade":            False,
        "packaging_state":        "sealed",
        "ingredients_raw":        parse_ingredients_from_off(off_data),
        "source":                 "open_food_facts",
    }


def extract_from_image(image_bytes: bytes, mime_type: str) -> dict:
    # Extract product information from an image using Gemini
    schema = {
        "type": "object",
        "properties": {
            "product_name":           {"type": ["string", "null"]},
            "barcode":                {"type": ["string", "null"]},
            "input_type":             {"type": "array", "items": {"type": "string"}},
            "is_commercial_packaged": {"type": "boolean"},
            "is_homemade":            {"type": "boolean"},
            "packaging_state":        {"type": "string"},
            "ingredients_raw":        {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "product_name", "barcode", "input_type",
            "is_commercial_packaged", "is_homemade",
            "packaging_state", "ingredients_raw",
        ],
    }

    prompt = """
You are a food product extraction assistant.
Look at the uploaded image and extract product facts only. Do NOT assess biosecurity.

Rules:
- packaging_state: sealed / open / unknown
- barcode: null if not clearly visible
- input_type: ["image"]
- ingredients_raw: only what is clearly visible or strongly implied; empty array if unsure
- Extract ONLY from what you can SEE in the image
- Do NOT hallucinate or assume standard recipes
- Do NOT add "flour", "sugar", "oil" unless clearly visible on packaging/label
- For packaged items, read the label if visible
- If unsure about ingredients, return empty array rather than guess

IMPORTANT - RICE IDENTIFICATION FROM APPEARANCE:
- RAW RICE: dry appearance, individual whole grains visible, NOT clumped together
  → Add "raw rice" or "uncooked rice" to ingredients (NOT just "rice")
  Example: If you see a bowl of dry individual grains → ingredient = "raw rice"
  
- COOKED RICE: soft moist texture, grains clumped/sticky, fluffy appearance
  → Add "cooked rice" to ingredients (NOT just "rice")
  Example: If you see fluffy/moist rice → ingredient = "cooked rice"

- RICE FLOUR/NOODLES/PRODUCTS: Fine powder or noodle form
  → Add "rice flour", "rice noodles", etc (be specific about form)

Return JSON only.
"""

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt,
        ],
        config={
            "response_mime_type": "application/json",
            "response_json_schema": schema,
            "temperature": 0,           # deterministic output — same input → same result
        },
    )

    data = json.loads(response.text)
    data["source"] = "gemini_image"
    return data


def extract_from_text(text: str) -> dict:
    # Extract product information from text input using Gemini
    schema = {
        "type": "object",
        "properties": {
            "product_name":           {"type": ["string", "null"]},
            "is_commercial_packaged": {"type": "boolean"},
            "is_homemade":            {"type": "boolean"},
            "ingredients_raw": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": [
            "product_name", "is_commercial_packaged",
            "is_homemade", "ingredients_raw",
        ],
    }

    prompt = f"""
You are a food ingredient extraction assistant for Australian border biosecurity.

The user is describing an item they want to bring into Australia.
Extract every ingredient or food component — explicitly stated AND strongly implied.

For named dishes (e.g. "sandwich", "curry", "sushi"), include typical ingredients.
For packaged products (e.g. "instant noodles"), include known ingredients.
Be thorough. Do not invent ingredients not implied by the input.

User input: "{text}"

Return valid JSON only.
"""

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": schema,
            "temperature": 0,           # deterministic output — same input → same result
        },
    )

    data = json.loads(response.text)
    data["source"]          = "text_input"
    data["input_type"]      = ["text"]
    data["barcode"]         = None
    data["packaging_state"] = "unknown"
    return data