"""
Module: Validation Method
Performs two-layer validation on images using enhanced validation prompts (EVP) and real blank/black image detection.
"""
from typing import Tuple, Any
from black_image_detector import is_single_color_image
from config import get_gpt_client
import json
import os
import base64
from PIL import Image
import io

# Error texts as per your production logic
ERROR_TEXTS = {
    "blank": "This image looks blank. Please retake.",
    "blurry": "Image is blurry. Please retake a clear photo.",
    "irrelevant": "Image doesn't match the question. Please retake.",
    "instruction": "Image doesn't follow the instructions. Please retake.",
    "unknown": "Unknown error. Please retake."
}

def encode_image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string for AI analysis"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Could not read image file {image_path}: {str(e)}")

def validate_image(image_path: str, evp: str, model_type: str = 'openai') -> Tuple[str, str]:
    """
    Validate the image using a two-layer process:
    Layer 1: Flag blank/dark images (not AI, uses is_single_color_image)
    Layer 2: AI-based analysis using EVP
    Returns: (status, description or error text)
    """
    # Validate input
    if not image_path or not isinstance(image_path, str):
        return ("Error", ERROR_TEXTS["blank"])
    
    if not os.path.exists(image_path):
        return ("Error", f"Image file not found: {image_path}")
    
    # Layer 1: Check for blank/dark image
    try:
        is_not_single_color = is_single_color_image(image_path)
        if not is_not_single_color:
            return ("Error", ERROR_TEXTS["blank"])
    except Exception as e:
        return ("Error", f"Error checking image quality: {str(e)}")
    
    # Layer 2: AI-based analysis using EVP
    try:
        gpt_client = get_gpt_client(model_type)
        
        # Encode image to base64 for AI analysis
        image_base64 = encode_image_to_base64(image_path)
        
        system_message = """You are a food safety validation AI. Analyze the provided image based on the Enhanced Validation Prompt (EVP) and return one of these specific cases:

1. "accepted" - Image is compliant and follows the EVP requirements
2. "blank" - Image appears blank, too dark, or shows nothing relevant
3. "blurry" - Image is blurry, unclear, or poor quality
4. "irrelevant" - Image doesn't match the question/requirement in the EVP
5. "instruction" - Image doesn't follow the specific instructions in the EVP

Return a JSON with fields: "case" (one of the above), "description" (short explanation of your assessment)"""
        
        user_message = f"EVP: {evp}\n\nAnalyze the image and determine if it meets the EVP requirements. Return the appropriate case and description."
        
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
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=200
        )
        
        # Parse the AI response
        result = json.loads(response.choices[0].message.content)
        case = result.get("case", "unknown")
        description = result.get("description", "")
        
        if case == "accepted":
            return ("Image Accepted", description)
        elif case in ERROR_TEXTS:
            return ("Error", ERROR_TEXTS[case])
        else:
            return ("Error", ERROR_TEXTS["unknown"])
            
    except Exception as e:
        # Fallback to unknown error if AI fails
        return ("Error", f"{ERROR_TEXTS['unknown']} (AI analysis failed: {str(e)})")

# Example usage:
if __name__ == "__main__":
    img_path = input("Enter image file path: ")
    evp = input("Enter EVP: ")
    model_type = input("Model type (default 'openai'): ") or "openai"
    status, description = validate_image(img_path, evp, model_type)
    print(f"Status: {status}")
    print(f"Description: {description}") 