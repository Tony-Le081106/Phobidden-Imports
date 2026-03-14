import os


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

def apply_classification_and_rules(base_data: dict) -> dict:
    classification = classify_for_rules(base_data)
    compare_input = {
        "categories":      classification["categories"],
        "attributes":      classification["attributes"],
        "ingredients_raw": base_data.get("ingredients_raw", []),
    }

    compare_result = compare_rules(compare_input)

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
    }

@app.route("/")
def home():
    return render_template("index.html")

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