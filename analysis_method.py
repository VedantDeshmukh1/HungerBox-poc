"""
Module: Analysis Method
Analyzes images based on Enhanced Insight Prompt (EIP) using AI (GPT) as in production code.
"""
from typing import Tuple, Dict, Any
from config import get_gpt_client
import json
import os
import base64
from enhanced_category_prompts import get_category_prompt
from validation_prompt_enhancer import enhance_validation_prompt

# Example: In future, fetch scoring and issue logic from DB
# def get_analysis_rules_from_db():
#     pass

def encode_image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string for AI analysis"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Could not read image file {image_path}: {str(e)}")

def analyze_image_with_ai(
    eip: str,
    image_path: str,
    category: str = None,
    expectation: str = None,
    model_type: str = "openai"
) -> Tuple[str, str, float, Dict[str, Any]]:
    """
    Analyze the image based on the EIP using GPT/AI and the correct category prompt template.

    Compliance Score Definition:
    ----------------------------
    The compliance score is a float value between 0 and 1 that quantifies how compliant the image is
    with respect to the provided insight prompt (EIP) and category expectations.

    - A score of **1.0** means the image is fully compliant with all requirements.
    - A score of **0.0** means the image is completely non-compliant.
    - Scores between 0 and 1 indicate partial compliance, with higher values reflecting better compliance.
    - The score should take into account the severity and number of issues found, as well as overall image quality.
    - This score is intended to provide a quick, quantitative measure of compliance for downstream processing, dashboards, or automated decision-making.

    Returns:
        - Compliance Status: Compliant/Non Compliant/Unable to determine
        - Description: Short description
        - Score: Compliance score (0-1, float)
        - JSON: {Critical Issue, Suggestion, plus all detailed fields}
    """
    try:
        gpt_client = get_gpt_client(model_type)
        # Use the category prompt template if category is provided
        if category:
            base_prompt = get_category_prompt(category, eip, expectation)
        else:
            base_prompt = eip

        # Enhance the prompt for AI
        enhanced_prompt = enhance_validation_prompt(base_prompt, model_type=model_type)

        # Add explicit output instructions for the AI
        output_instructions = (
            "\n\nIMPORTANT: Your response MUST be a single JSON object with the following fields:\n"
            " - compliance_status: 'Compliant', 'Non Compliant', or 'Unable to determine'\n"
            " - description: Short summary of your assessment\n"
            " - score: Compliance score (0-1, float)\n"
            " - critical_issue: The most critical issue found (string, or empty if none)\n"
            " - suggestion: Actionable suggestion for improvement (string, or empty if none)\n"
            " - criteria_met: 'Yes' or 'No' (for compliance with standards)\n"
            " - explanation: 2-3 sentence explanation\n"
            " - improvements: Specific actionable recommendations\n"
            " - severity: 'Critical', 'Major', 'Minor', or 'None'\n"
            " - image_quality_issues: List of quality issues (e.g., ['too_dark', 'too_blurry'] or ['none'])\n"
            " - quality_assessment: Brief comment on image quality\n"
            " - tags: List of 3-5 tags\n"
            "If a field is not applicable, use an empty string or a suitable default."
        )
        final_prompt = enhanced_prompt + output_instructions

        # Encode image to base64 for AI analysis
        image_base64 = encode_image_to_base64(image_path)
        system_message = (
            "You are a food safety compliance AI. Analyze the image and EIP, and return a robust JSON as instructed."
        )
        user_message = final_prompt
        response = gpt_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.2,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        # Parse the result
        try:
            result = json.loads(response.choices[0].message.content)
            # Fallbacks for missing fields
            status = result.get("compliance_status", result.get("criteria_met", "Unable to determine"))
            description = result.get("description", result.get("explanation", ""))
            score = float(result.get("score", 0))
            result_json = {
                "Critical Issue": result.get("critical_issue", ""),
                "Suggestion": result.get("suggestion", ""),
                "criteria_met": result.get("criteria_met", ""),
                "explanation": result.get("explanation", ""),
                "improvements": result.get("improvements", ""),
                "severity": result.get("severity", ""),
                "image_quality_issues": result.get("image_quality_issues", []),
                "quality_assessment": result.get("quality_assessment", ""),
                "tags": result.get("tags", []),
            }
        except Exception as e:
            status = "Unable to determine"
            description = f"AI response parsing error: {str(e)}"
            score = 0.0
            result_json = {"Critical Issue": "AI error", "Suggestion": "Check input and try again."}
        return status, description, score, result_json
    except Exception as e:
        # Fallback to old logic if anything fails
        status = "Unable to determine"
        description = f"AI analysis failed: {str(e)}"
        score = 0.0
        result_json = {"Critical Issue": "AI error", "Suggestion": "Check input and try again."}
        return status, description, score, result_json

# Example usage:
if __name__ == "__main__":
    img_path = input("Enter image file path: ")
    eip = input("Enter EIP: ")
    category = input("Enter category (optional): ") or None
    expectation = input("Enter expectation (optional): ") or None
    model_type = input("Model type (default 'openai'): ") or "openai"
    print(analyze_image_with_ai(eip, img_path, category, expectation, model_type)) 