import os
import json

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from google import genai

from function.classification import classify_for_rules
from function.compare import compare_rules
from function.ingredient_extraction import (
    detect_barcode,
    get_product_by_barcode,
    parse_ingredients_from_off,
    build_off_base,
    extract_from_image,
    extract_from_text
)

load_dotenv()

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

def allowed_file_mime(mime_type: str):
    return mime_type in {"image/jpeg", "image/png", "image/webp"}


def enrich_verdict(base_data: dict, compare_result: dict) -> dict:
    """
    Gemini writes verdict_reason + key_concerns based on the rule-engine output.
    Does NOT override the verdict — just makes it human-readable.
    """
    schema = {
        "type": "object",
        "properties": {
            "verdict_reason": {"type": "string"},
            "key_concerns":   {"type": "array", "items": {"type": "string"}},
        },
        "required": ["verdict_reason", "key_concerns"],
    }

    prompt = f"""
You are an Australian biosecurity advisor writing traveller-facing guidance.

Product: {base_data.get("product_name") or "Unknown"}
Ingredients: {', '.join(base_data.get("ingredients_raw", []))}

The rule engine has determined:
  Verdict:          {compare_result["overall_verdict"]}
  Matched rules:    {', '.join(compare_result["matched_rules"])}
  Rule reasons:     {json.dumps(compare_result["reasons"])}

Your task:
1. verdict_reason — one sentence explaining WHY this verdict applies to THIS product.
   Be specific: name the problematic ingredients or category. Do not just copy the rule text.
   Keep it simple and direct.

2. key_concerns — 2 to 4 short actionable bullet points for the traveller:
   - For BRING_IT:    what to still watch out for (quantity limits, declare-if-unsure risks)
   - For DECLARE_IT:  exactly what the traveller should do at border customs
   - For DONT_BRING:  why it's prohibited and what happens if confiscated

Keep language simple, helpful, and direct. Avoid jargon. Return valid JSON only.
"""

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": schema,
            "temperature": 0,
        },
    )

    return json.loads(response.text)


def apply_classification_and_rules(base_data: dict) -> dict:
    classification = classify_for_rules(base_data)
    compare_input = {
        "categories":      classification["categories"],
        "attributes":      classification["attributes"],
        "ingredients_raw": base_data.get("ingredients_raw", []),
    }

    compare_result = compare_rules(compare_input)

    # Enrich with human-readable explanations
    enrichment = enrich_verdict(base_data, compare_result)

    return {
        **base_data,
        "categories":        classification["categories"],
        "category_matches":  classification["category_matches"],
        "attributes":        classification["attributes"],
        "overall_verdict":   compare_result["overall_verdict"],
        "matched_rules":     compare_result["matched_rules"],
        "reasons":           compare_result["reasons"],
        "condition_reports": compare_result["condition_reports"],
        "rules_applied":     compare_result["rules_applied"],
        "verdict_reason":    enrichment["verdict_reason"],
        "key_concerns":      enrichment["key_concerns"],
    }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about-us")
def about_us():
    return render_template("about-us.html")

@app.route("/user-reports")
def user_reports():
    return render_template("user-reports.html")

@app.route("/check-text", methods=["POST"])
def check_text():
    # check product description

    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        base_data = extract_from_text(text)
        result    = apply_classification_and_rules(base_data)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/check-barcode", methods=["POST"])
def check_barcode():

    body = request.get_json(silent=True) or {}
    barcode = (body.get("barcode") or "").strip()

    if not barcode:
        return jsonify({"error": "No barcode provided"}), 400

    try:
        off_data = get_product_by_barcode(barcode)

        # open food facts
        if off_data.get("product"):
            base_data = build_off_base(barcode, off_data)

        # barcode not found
        else:
            base_data = {
                "product_name": None,
                "barcode": barcode,
                "input_type": ["barcode"],
                "is_commercial_packaged": True,
                "is_homemade": False,
                "packaging_state": "unknown",
                "ingredients_raw": [],
                "source": "barcode_not_found",
            }

        result = apply_classification_and_rules(base_data)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        barcode = detect_barcode(image_bytes)

        if barcode:
            off_data = get_product_by_barcode(barcode)

            # open food facts 
            if off_data.get("product"):
                result = build_off_base(barcode, off_data)
                return jsonify(apply_classification_and_rules(result))

            # gemini fallback when data not found
            base_data = extract_from_image(image_bytes, mime_type)
            base_data["barcode"] = barcode
            base_data["source"]  = "gemini_fallback_after_barcode"
            return jsonify(apply_classification_and_rules(base_data))

        # no barcode gemini
        base_data = extract_from_image(image_bytes, mime_type)
        return jsonify(apply_classification_and_rules(base_data))

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug=True)