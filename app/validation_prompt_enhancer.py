"""
Module: Validation Prompt Enhancer
Enhances validation prompts to be more actionable and AI-analyzable, using real prompt structure.
"""
from typing import Optional
from config import get_gpt_client
import json

# Example: In future, fetch enhancement rules/templates from DB
# def get_enhancement_template_from_db():
#     pass

# Real enhancement logic based on your prompt structure
ENHANCEMENT_GUIDANCE = (
    "\n\nIMPORTANT: Ensure the prompt is clear, specific, and actionable. "
    "Include instructions for image quality (e.g., too dark, too blurry), "
    "and specify what compliance looks like. If the question allows a blank or empty image, "
    "state this explicitly."
)

def enhance_validation_prompt(prompt: str, extra_guidance: Optional[str] = None, model_type: str = "openai") -> str:
    """
    Enhance the given validation prompt to make it more specific and actionable for AI analysis.
    Uses GPT/AI if available, otherwise falls back to static enhancement.
    """
    try:
        gpt_client = get_gpt_client(model_type)
        system_message = "You are an expert prompt engineer. Enhance the following validation prompt to be clear, specific, actionable, and AI-analyzable."
        user_message = prompt.strip() + ENHANCEMENT_GUIDANCE
        if extra_guidance:
            user_message += f"\n\nAdditional Guidance: {extra_guidance}"
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
    except Exception as e:
        # Fallback to static enhancement
        enhanced = prompt.strip() + ENHANCEMENT_GUIDANCE
        if extra_guidance:
            enhanced += f"\n\nAdditional Guidance: {extra_guidance}"
        enhanced += f"\n\n[AI enhancement failed: {str(e)}]"
        return enhanced

# Example usage:
if __name__ == "__main__":
    prompt = input("Enter validation prompt: ")
    extra = input("Extra guidance (optional): ")
    model_type = input("Model type (default 'openai'): ") or "openai"
    print(enhance_validation_prompt(prompt, extra, model_type)) 