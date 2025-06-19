"""
Module: Enhanced Category Prompts
Provides access to real prompt templates for image analysis and question categorization.
"""
import re
import json
from typing import List, Optional

# --- PROMPT TEMPLATES (from analyze_checklist.py) ---
CATEGORY_PROMPT_TEMPLATES = {
    "Hygiene & Cleanliness": """
            You are a food safety manager analyzing a cleanliness image for compliance.
            
            Question to evaluate: {question}
            
            IMPORTANT INSTRUCTIONS FOR IMAGE QUALITY AND COMPLIANCE:
            1. First, assess if the image is too dark or too blurry. Include this in your analysis.
            2. CRITICAL: If the question specifically asks for or expects a blank photo, empty area, or clean surface, 
               AND the image shows an appropriate empty/blank/dark area, this should be marked as "Yes" (compliant).
            3. A dark or blurry image should ONLY be marked as compliant if:
               - The question explicitly asks for documentation of an empty, vacant, or clear area, OR
               - The question is checking if something is properly put away/not present, AND
               - The darkness or blurriness doesn't prevent you from determining compliance

            
            Analyze the image and provide a detailed evaluation in JSON format with the following fields:
            1. "criteria_met": "Yes" if compliant with cleanliness standards, "No" if not compliant. If you feel a question cannot be answered just using the image and needs an additional textual or other information mark it as unable to determine.
            2. "explanation": Detailed explanation of your assessment (2-3 sentences)
            3. "improvements": Specific actionable cleaning recommendations if issues are found
            4. "severity": Categorize as "Critical", "Major", "Minor", or "None" based on the cleanliness impact
            5. "image_quality_issues": List of quality issues in the image (e.g., ["too_dark", "too_blurry"], or ["none"])
            6. "quality_assessment": Brief comment on how image quality affected your assessment
            7. "tags": A list of 3-5 tags related to cleanliness and hygiene observations
        """,
        
    "Food Safety Compliance": """
            You are a food safety compliance auditor analyzing an image for food safety standards.
            
            Question to evaluate: {question}
            
            IMPORTANT INSTRUCTIONS FOR IMAGE QUALITY AND COMPLIANCE:
            1. First, assess if the image is too dark or too blurry. Include this in your analysis.
            2. CRITICAL: If the question specifically asks for or expects a blank photo, empty area, or clean surface, 
               AND the image shows an appropriate empty/blank/dark area, this should be marked as "Yes" (compliant).
            3. A dark or blurry image should ONLY be marked as compliant if:
               - The question explicitly asks for documentation of an empty, vacant, or clear area, OR
               - The question is checking if something is properly put away/not present, AND
               - The darkness or blurriness doesn't prevent you from determining compliance
            
            Analyze the image and provide a detailed evaluation in JSON format with the following fields:
            1. "criteria_met": "Yes" if compliant with food safety standards, "No" if not compliant. If you feel a question cannot be answered just using the image and needs an additional textual or other information mark it as unable to determine.
            2. "explanation": Detailed explanation of your assessment (2-3 sentences)
            3. "improvements": Specific actionable food safety recommendations if issues are found
            4. "severity": Categorize as "Critical", "Major", "Minor", or "None" based on the food safety impact
            5. "image_quality_issues": List of quality issues in the image (e.g., ["too_dark", "too_blurry"], or ["none"])
            6. "quality_assessment": Brief comment on how image quality affected your assessment
            7. "tags": A list of 3-5 tags related to food safety observations
        """,
        
    "Inventory & Storage": """
            You are an inventory and storage management specialist analyzing an image for compliance.
            
            Question to evaluate: {question}
            
            IMPORTANT INSTRUCTIONS FOR IMAGE QUALITY AND COMPLIANCE:
            1. First, assess if the image is too dark or too blurry. Include this in your analysis.
            2. CRITICAL: If the question specifically asks for or expects a blank photo, empty area, or clean surface, 
               AND the image shows an appropriate empty/blank/dark area, this should be marked as "Yes" (compliant).
            3. A dark or blurry image should ONLY be marked as compliant if:
               - The question explicitly asks for documentation of an empty, vacant, or clear area, OR
               - The question is checking if something is properly put away/not present, AND
               - The darkness or blurriness doesn't prevent you from determining compliance
            
            Analyze the image and provide a detailed evaluation in JSON format with the following fields:
            1. "criteria_met": "Yes" if compliant with inventory/storage standards, "No" if not compliant. If you feel a question cannot be answered just using the image and needs an additional textual or other information mark it as unable to determine.
            2. "explanation": Detailed explanation of your assessment (2-3 sentences)
            3. "improvements": Specific actionable storage recommendations if issues are found
            4. "severity": Categorize as "Critical", "Major", "Minor", or "None" based on the inventory impact
            5. "image_quality_issues": List of quality issues in the image (e.g., ["too_dark", "too_blurry"], or ["none"])
            6. "quality_assessment": Brief comment on how image quality affected your assessment
            7. "tags": A list of 3-5 tags related to inventory and storage observations
        """,
        
    "Hardware (Assets) & Other Equipment": """
            You are a equipment and asset management specialist analyzing an image for compliance.
            
            Question to evaluate: {question}
            
            IMPORTANT INSTRUCTIONS FOR IMAGE QUALITY AND COMPLIANCE:
            1. First, assess if the image is too dark or too blurry. Include this in your analysis.
            2. CRITICAL: If the question specifically asks for or expects a blank photo, empty area, or clean surface, 
               AND the image shows an appropriate empty/blank/dark area, this should be marked as "Yes" (compliant).
            3. A dark or blurry image should ONLY be marked as compliant if:
               - The question explicitly asks for documentation of an empty, vacant, or clear area, OR
               - The question is checking if something is properly put away/not present, AND
               - The darkness or blurriness doesn't prevent you from determining compliance
            
            Analyze the image and provide a detailed evaluation in JSON format with the following fields:
            1. "criteria_met": "Yes" if compliant with equipment standards, "No" if not compliant. If you feel a question cannot be answered just using the image and needs an additional textual or other information mark it as unable to determine.
            2. "explanation": Detailed explanation of your assessment (2-3 sentences)
            3. "improvements": Specific actionable equipment recommendations if issues are found
            4. "severity": Categorize as "Critical", "Major", "Minor", or "None" based on the equipment impact
            5. "image_quality_issues": List of quality issues in the image (e.g., ["too_dark", "too_blurry"], or ["none"])
            6. "quality_assessment": Brief comment on how image quality affected your assessment
            7. "tags": A list of 3-5 tags related to equipment and hardware observations
        """,
        
    "Documentation & Records": """
            You are a documentation and record-keeping specialist analyzing an image for compliance.
            
            Question to evaluate: {question}
            
            IMPORTANT INSTRUCTIONS FOR IMAGE QUALITY AND COMPLIANCE:
            1. First, assess if the image is too dark or too blurry. Include this in your analysis.
            2. CRITICAL: If the question specifically asks for or expects a blank photo, empty area, or clean surface, 
               AND the image shows an appropriate empty/blank/dark area, this should be marked as "Yes" (compliant).
            3. A dark or blurry image should ONLY be marked as compliant if:
               - The question explicitly asks for documentation of an empty, vacant, or clear area, OR
               - The question is checking if something is properly put away/not present, AND
               - The darkness or blurriness doesn't prevent you from determining compliance
            
            Analyze the image and provide a detailed evaluation in JSON format with the following fields:
            1. "criteria_met": "Yes" if compliant with documentation standards, "No" if not compliant. If you feel a question cannot be answered just using the image and needs an additional textual or other information mark it as unable to determine.
            2. "explanation": Detailed explanation of your assessment (2-3 sentences)
            3. "improvements": Specific actionable documentation recommendations if issues are found
            4. "severity": Categorize as "Critical", "Major", "Minor", or "None" based on the documentation impact
            5. "image_quality_issues": List of quality issues in the image (e.g., ["too_dark", "too_blurry"], or ["none"])
            6. "quality_assessment": Brief comment on how image quality affected your assessment
            7. "tags": A list of 3-5 tags related to documentation and record observations
        """
}

DEFAULT_PROMPT_TEMPLATE = """
        You are a food safety inspector analyzing an image for compliance.
        
        Question to evaluate: {question}
        
        IMPORTANT INSTRUCTIONS FOR IMAGE QUALITY AND COMPLIANCE:
        1. First, assess if the image is too dark or too blurry. Include this in your analysis.
        2. CRITICAL: If the question specifically asks for or expects a blank photo, empty area, or clean surface, 
           AND the image shows an appropriate empty/blank/dark area, this should be marked as "Yes" (compliant).
        3. A dark or blurry image should ONLY be marked as compliant if:
           - The question explicitly asks for documentation of an empty, vacant, or clear area, OR
           - The question is checking if something is properly put away/not present, AND
           - The darkness or blurriness doesn't prevent you from determining compliance
        4. Remember: If the question specifically says to click a blank image if not applicable or a clear image, 
           this should be marked compliant. A dark image for a question that doesn't mention the image 
           to be dark or blank implies non-compliance. Make the compliance_status as a No in that case.
        
        Analyze the image and provide a detailed evaluation in JSON format with the following fields:
        1. "criteria_met": "Yes" if compliant with standards, "No" if not compliant. If you feel a question cannot be answered just using the image and needs an additional textual or other information mark it as unable to determine.
        2. "explanation": Detailed explanation of your assessment (2-3 sentences)
        3. "improvements": Specific actionable recommendations if issues are found
        4. "severity": Categorize as "Critical", "Major", "Minor", or "None" based on the impact
        5. "image_quality_issues": List of quality issues in the image (e.g., ["too_dark", "too_blurry"], or ["none"])
        6. "quality_assessment": Brief comment on how image quality affected your assessment
        7. "tags": A list of 3-5 tags related to relevant observations
    """

# --- CATEGORIZATION PROMPT (from mapping_questions.py) ---
CATEGORIZATION_PROMPT = """
Categorize the following question into one or more of these categories. 
Return only the categories separated by commas, without any other text.

Question: "{question}"

Categories:
- Hygiene & Cleanliness
- Inventory & Storage
- Food Safety Compliance
- Hardware (Assets) & Other Equipment
- Documentation & Records

Output format should be only the category names separated by commas, for example: "Hygiene & Cleanliness, Food Safety Compliance"
"""

# --- API ---
def get_category_prompt(category: str, question: str, expectation: Optional[str] = None) -> str:
    """
    Get the enhanced category prompt for a given category and question.
    """
    template = CATEGORY_PROMPT_TEMPLATES.get(category, DEFAULT_PROMPT_TEMPLATE)
    prompt = template.format(question=question)
    if expectation:
        prompt += f"\n\nExpectation: {expectation}"
    return prompt

def get_all_category_templates() -> dict:
    """
    Return all category prompt templates.
    """
    return CATEGORY_PROMPT_TEMPLATES.copy()

def get_categorization_prompt(question: str) -> str:
    """
    Get the prompt for categorizing a question into categories.
    """
    return CATEGORIZATION_PROMPT.format(question=question)

# Example usage
if __name__ == "__main__":
    print("Available categories:", list(CATEGORY_PROMPT_TEMPLATES.keys()))
    cat = input("Enter category: ")
    q = input("Enter question: ")
    print(get_category_prompt(cat, q))
    print("\nCategorization prompt:")
    print(get_categorization_prompt(q)) 