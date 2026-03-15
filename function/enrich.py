import os
import json

from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


def enrich_verdict(base_data: dict, compare_result: dict) -> dict:
    """
    Gemini writes verdict_reason + key_concerns based on the rule-engine output.
    Does NOT override the verdict — just makes it human-readable.
    
    Args:
        base_data: Product information (product_name, ingredients_raw, etc.)
        compare_result: Rule comparison output (overall_verdict, matched_rules, reasons)
    
    Returns:
        dict with 'verdict_reason' and 'key_concerns'
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
