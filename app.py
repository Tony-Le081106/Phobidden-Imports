import os


from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from google import genai

from function.classification import classify_ingredients_to_categories
from function.compare import compare_rules
from function.ingredient_extraction import (
    detect_barcode,
    get_product_by_barcode,
    parse_ingredients_from_off,
    build_off_response,
    analyze_with_gemini
)

load_dotenv()

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

def allowed_file_mime(mime_type: str):
    return mime_type in {"image/jpeg", "image/png", "image/webp"}

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