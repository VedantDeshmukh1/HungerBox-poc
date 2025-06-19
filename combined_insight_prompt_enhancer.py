"""
Module: Combined Insight Prompt Enhancer
Combines and enhances insight and category prompts using AI (GPT) as in production code.
"""
from typing import Optional
from config import get_gpt_client

# Example: In future, fetch enhancement logic from DB
# def get_combined_enhancement_from_db():
#     pass

def enhance_combined_insight_prompt(insight_prompt: str, category_prompt: str, model_type: str = "openai") -> str:
    """
    Combine and enhance the insight and category prompts using GPT/AI.
    Uses the same approach as in analyze_checklist.py and streamlit_app.py.
    """
    gpt_client = get_gpt_client(model_type)
    system_message = "You are an expert prompt engineer. Combine and enhance the following insight and category prompts into a single, actionable, AI-analyzable prompt."
    user_message = f"Category Prompt: {category_prompt}\nInsight Prompt: {insight_prompt}\n\nReturn a single enhanced prompt."
    response = gpt_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        temperature=0.2,
        max_tokens=400
    )
    enhanced = response.choices[0].message.content.strip()
    return enhanced

# Example usage:
if __name__ == "__main__":
    insight = input("Enter insight prompt: ")
    category = input("Enter category prompt: ")
    print(enhance_combined_insight_prompt(insight, category)) 