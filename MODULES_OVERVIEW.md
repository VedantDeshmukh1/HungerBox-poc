# 📦 HungerBox Modules Overview

A quick reference for what each module in this project does, with real-life examples for every key function. Use this as a handy guide to understand and test each part of the system.

---

| Module | Purpose | Example Usage |
|--------|---------|--------------|
| [config.py](#configpy) | Sets up and authenticates the GPT client (OpenAI). | Get a GPT client for API calls |
| [enhanced_category_prompts.py](#enhanced_category_promptspy) | Provides category-specific prompt templates. | Build a prompt for a hygiene question |
| [validation_prompt_enhancer.py](#validation_prompt_enhancerpy) | Enhances prompts to be more actionable for AI. | Make a prompt more specific and AI-ready |
| [black_image_detector.py](#black_image_detectorpy) | Detects if an image is blank or mostly a single color. | Check if an image is blank |
| [validation_method.py](#validation_methodpy) | Two-layer image validation: blank check + AI compliance. | Validate an image for compliance |
| [analysis_method.py](#analysis_methodpy) | Full AI-based compliance analysis and scoring. | Analyze an image and get compliance JSON |
| [combined_insight_prompt_enhancer.py](#combined_insight_prompt_enhancerpy) | Combines and enhances insight/category prompts. | Merge two prompts for advanced use |

---

## config.py
**Purpose:** Sets up and authenticates the GPT client (OpenAI).

**Example:**
```python
from config import get_gpt_client
client = get_gpt_client("openai")
print(client)  # Should print the OpenAI client object
```

---

## enhanced_category_prompts.py
**Purpose:** Provides category-specific prompt templates for hygiene, safety, etc.

**Example:**
```python
from enhanced_category_prompts import get_category_prompt
category = "Hygiene & Cleanliness"
question = "Are the bins separated?"
expectation = "Bins should be at least 1 meter apart."
prompt = get_category_prompt(category, question, expectation)
print(prompt)
```

---

## validation_prompt_enhancer.py
**Purpose:** Enhances prompts to be more actionable and AI-analyzable.

**Example:**
```python
from validation_prompt_enhancer import enhance_validation_prompt
prompt = "Bins should be at least 1 meter apart."
enhanced = enhance_validation_prompt(prompt)
print(enhanced)
```

---

## black_image_detector.py
**Purpose:** Detects if an image is blank or mostly a single color.

**Example:**
```python
from black_image_detector import is_single_color_image
result = is_single_color_image("2225563_1741760657.jpg")
print("Is image NOT blank?", result)  # True means image is NOT blank
```

---

## validation_method.py
**Purpose:** Two-layer image validation: blank/dark check, then AI compliance.

**Example:**
```python
from validation_method import validate_image
img_path = "2225563_1741760657.jpg"
ev_prompt = "Bins should be at least 1 meter apart."
status, description = validate_image(img_path, ev_prompt)
print("Status:", status)
print("Description:", description)
```

---

## analysis_method.py
**Purpose:** Full AI-based compliance analysis and scoring, returns detailed JSON.

**Example:**
```python
from analysis_method import analyze_image_with_ai
img_path = "2225563_1741760657.jpg"
prompt = "Bins should be at least 1 meter apart."
category = "Hygiene & Cleanliness"
expectation = "Bins should be at least 1 meter apart."
status, description, score, result_json = analyze_image_with_ai(prompt, img_path, category, expectation)
print("Status:", status)
print("Description:", description)
print("Score:", score)
print("Result JSON:", result_json)
```

---

## combined_insight_prompt_enhancer.py
**Purpose:** Combines and enhances an insight prompt and a category prompt using AI.

**Example:**
```python
from combined_insight_prompt_enhancer import enhance_combined_insight_prompt
insight = "Are the bins separated?"
category_prompt = "Bins should be at least 1 meter apart."
combined = enhance_combined_insight_prompt(insight, category_prompt)
print(combined)
```

---

# 🧪 Real-Life Example: Full Pipeline

Suppose you want to check if bins in a cafeteria are separated as per hygiene standards:

```python
from config import get_gpt_client
from enhanced_category_prompts import get_category_prompt
from validation_prompt_enhancer import enhance_validation_prompt
from validation_method import validate_image
from analysis_method import analyze_image_with_ai

img_path = "2225563_1741760657.jpg"
category = "Hygiene & Cleanliness"
question = "Are the bins separated?"
expectation = "Bins should be at least 1 meter apart."

# 1. Build the category prompt
base_prompt = get_category_prompt(category, question, expectation)

# 2. Enhance the prompt for AI
enhanced_prompt = enhance_validation_prompt(base_prompt)

# 3. Validate the image (blank/dark + AI compliance)
status, description = validate_image(img_path, enhanced_prompt)
if status == "Error":
    print("Validation failed:", description)
else:
    # 4. Full AI analysis
    status, description, score, result_json = analyze_image_with_ai(enhanced_prompt, img_path, category, expectation)
    print("Analysis Status:", status)
    print("Description:", description)
    print("Score:", score)
    print("Result JSON:", result_json)
```

---

**Tip:** You can copy-paste any example above into a Python file in this directory and run it (after setting up your OpenAI API key and dependencies). 