import os
from config import get_gpt_client
from enhanced_category_prompts import get_category_prompt
from validation_prompt_enhancer import enhance_validation_prompt
from validation_method import validate_image
from analysis_method import analyze_image_with_ai

def log_step(title, content=None):
    print("\n" + "="*60)
    print(f"STEP: {title}")
    if content is not None:
        print(content)
    print("="*60 + "\n")

def main():
    # 0. Config and API Key
    log_step("Config: Get GPT Client and API Key")
    try:
        client = get_gpt_client("openai")
        api_key = getattr(client, "api_key", None)
        print(f"OpenAI API Key loaded: {'Yes' if api_key else 'No'}")
    except Exception as e:
        print(f"Error loading GPT client: {e}")
        return

    # 1. Inputs
    img_path = "2225563_1741760657.jpg"
    category = "Hygiene & Cleanliness"
    question = "Are the bins separated?"
    expectation = "Are the bins overflowing?"
    print(f"Image Path: {img_path}")
    print(f"Category: {category}")
    print(f"Question: {question}")
    print(f"Expectation: {expectation}")

    # 2. Build category prompt
    log_step("Build Category Prompt")
    base_prompt = get_category_prompt(category, question, expectation)
    print("Base Prompt:\n", base_prompt)

    # 3. Enhance prompt for AI
    log_step("Enhance Prompt for AI")
    enhanced_prompt = enhance_validation_prompt(base_prompt)
    print("Enhanced Prompt:\n", enhanced_prompt)

    # 4. Validate image (Layer 1: blank/dark, Layer 2: AI compliance)
    log_step("Validate Image (Blank/Dark + AI Compliance)")
    status, description = validate_image(img_path, enhanced_prompt)
    print(f"Validation Status: {status}")
    print(f"Validation Description: {description}")

    # If validation fails, stop the pipeline
    if status == "Error":
        print("\n!!! Pipeline stopped: Image validation failed. Reason:")
        print(f"    {description}")
        print("Please retake the image and try again.")
        log_step("Summary")
        print("Pipeline terminated due to validation error.")
        return

    # 5. Full AI Analysis (compliance, score, suggestions, all fields)
    log_step("Full AI Analysis (Compliance, Score, Suggestions, All Fields)")
    status, description, score, result_json = analyze_image_with_ai(
        enhanced_prompt, img_path, category, expectation
    )
    print(f"Analysis Status: {status}")
    print(f"Analysis Description: {description}")
    print(f"Analysis Score: {score}")
    print("Analysis Result JSON (all fields):")
    for k, v in result_json.items():
        print(f"  {k}: {v}")

    # 6. Summary
    log_step("Summary")
    print("All steps completed. See above for detailed logs and outputs.")

if __name__ == "__main__":
    main()