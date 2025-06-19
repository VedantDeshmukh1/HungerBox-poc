# 📟 Image Compliance Analysis System: Documentation

## 📌 Overview

This project is a food safety AI analysis system that takes user-submitted images and evaluates them for compliance using GPT-based models. It leverages prompt engineering, validation layers, and structured outputs to assist food safety teams in maintaining high standards.

---

## 🗂️ Table of Contents

| Section | Description |
|---------|-------------|
| [Overview](#-overview) | Project summary and purpose |
| [Shortform Definitions](#-shortform-definitions) | Key terms and abbreviations |
| [Core Components](#-core-components) | Main modules and their functions |
| [Data Flow Diagram (with Example)](#-data-flow-diagram-with-example) | Step-by-step workflow and use case |
| [Sample JSON Output](#-sample-json-output) | Example of AI output format |
| [Example Execution](#-example-execution) | How to run the main analysis script |
| [Testing the Full Workflow: test_hb_modules.py](#-testing-the-full-workflow-test_hb_modulespy) | How to run and understand the test script |
| [Dependencies](#-dependencies) | Required packages and versions |
| [Security & API Keys](#-security--api-keys) | API key setup and security notes |
| [Authors](#-authors) | Project contributors |
| [Future Enhancements](#-future-enhancements) | Planned improvements |

---

## 🖉 Shortform Definitions

- **EIP**: Enhanced Insight Prompt — A category-specific prompt template (e.g., for hygiene, documentation) selected using the question and optional expectation. Built using `get_category_prompt()` from `enhanced_category_prompts.py`.
- **EVP**: Enhanced Validation Prompt — A stricter prompt based on EIP or user input, improved via `enhance_validation_prompt()` in `validation_prompt_enhancer.py`.
- **Final Prompt**: The EIP (or category prompt) enhanced into EVP, further combined with output instructions before sending to GPT.
- **GPT**: Generative Pretrained Transformer — the AI model (OpenAI's GPT-4o) used for reasoning, validation, and scoring.

---

## 🧩 Core Components

### 1. **analysis\_method.py**

**Purpose:**

- Performs main AI-based compliance evaluation of an image based on the Enhanced Insight Prompt (EIP).

**Key Functions:**

- `analyze_image_with_ai()`:
  - Generates base prompt from `get_category_prompt()` if category is supplied.
  - Enhances the base prompt into EVP using `enhance_validation_prompt()`.
  - Appends output formatting instructions to create the **Final Prompt**.
  - Encodes image in base64.
  - Sends data to GPT via `config.py` and parses structured JSON response.

**Returns:**

- Compliance status
- Description
- Compliance score
- Detailed assessment JSON

---

### 2. **black\_image\_detector.py**

**Purpose:**

- Identifies if an image is mostly blank or of a single color (e.g. completely black).

**Key Function:**

- `is_single_color_image()`:
  - Calculates pixel variance to determine if image is visually informative.

---

### 3. **combined\_insight\_prompt\_enhancer.py**

**Purpose:**

- Merges and enhances an insight prompt and category prompt into one GPT-optimized instruction.

**Key Function:**

- `enhance_combined_insight_prompt()`
- Used only if prompts are provided separately and need merging (not used in final validation pipeline).

---

### 4. **config.py**

**Purpose:**

- Sets up and authenticates the GPT model.

**Key Function:**

- `get_gpt_client()`
  - Loads OpenAI API key.
  - Returns the `openai` client object for use in all AI modules.

---

### 5. **enhanced\_category\_prompts.py**

**Purpose:**

- Provides category-specific prompts and templates for hygiene, safety, inventory, etc.

**Key Functions:**

- `get_category_prompt()` → Creates the **EIP** (base template) using category and question.
- `get_all_category_templates()`
- `get_categorization_prompt()`

---

### 6. **validation\_method.py**

**Purpose:**

- Performs two-layer validation on images:
  - **Layer 1:** Blank detection via `black_image_detector.py`
  - **Layer 2:** AI-powered validation using EVP

**Key Function:**

- `validate_image()`:
  - Checks blank image using pixel distribution.
  - Sends image + EVP prompt to GPT with fixed response options.

---

### 7. **validation\_prompt\_enhancer.py**

**Purpose:**

- Enhances any prompt into a cleaner, AI-readable **EVP** format.

**Key Function:**

- `enhance_validation_prompt()`

---

## 🧐 Data Flow Diagram (with Example)

### 📅 Use Case:

User uploads an image of a hamburger with the question: **"Is the food item protected from contamination?"**

### 🔄 Step-by-Step Flow

```
[1] User Input
    └─ Question: "Is the food item protected from contamination?"
    └─ Image: hamburger.jpg

[2] validation_method.py
    └─ Check if image path is valid
    └─ Check if image is blank (via black_image_detector.py)
        └─ If >50% pixels are same color → "Error: This image looks blank. Please retake."
    └─ If not blank → continue to EVP check
    └─ EVP prompt sent to GPT with image in base64
    └─ GPT returns one of:
        - "accepted"
        - "blank"
        - "blurry"
        - "irrelevant"
        - "instruction"
    └─ If not accepted → mapped to error using ERROR_TEXTS

[3] enhanced_category_prompts.py
    └─ Choose template for "Food Safety Compliance"
    └─ Use `get_category_prompt()` to build **EIP** with question and expectation

[4] validation_prompt_enhancer.py
    └─ Input: EIP
    └─ Output: Enhanced as **EVP** (adds image quality and compliance instructions)

[5] analysis_method.py
    └─ Appends structured JSON instructions to EVP → **Final Prompt**
    └─ Encodes image in base64
    └─ Sends final prompt and image to GPT using config.py

[6] GPT Response
    └─ Structured JSON with:
        - compliance_status
        - description
        - score (0–1)
        - issues, suggestions, quality analysis

[7] Final Output
    └─ Shown to user or fed to downstream automation/dashboard
    └─ Example:
        - Compliance: Compliant
        - Description: "The hamburger is wrapped securely and placed on a clean surface."
        - Score: 1.0
```

---

## 📅 Sample JSON Output

```json
{
  "compliance_status": "Compliant",
  "description": "The hamburger is wrapped securely and placed on a clean surface.",
  "score": 1.0,
  "critical_issue": "",
  "suggestion": "",
  "criteria_met": "Yes",
  "explanation": "All food safety requirements were met.",
  "improvements": "",
  "severity": "None",
  "image_quality_issues": ["none"],
  "quality_assessment": "Good lighting and focus.",
  "tags": ["clean", "wrapped", "safe"]
}
```

---

## 🛠️ Example Execution

```bash
$ python analysis_method.py
Enter image file path: example.jpg
Enter EIP: Is the food item protected from contamination?
Enter category (optional): Food Safety Compliance
Model type (default 'openai'): openai
```

---

## 🧪 Testing the Full Workflow: test_hb_modules.py

This script demonstrates the end-to-end workflow of the image compliance analysis system, including prompt building, validation, and AI analysis. It is useful for testing and understanding the pipeline.

### How to Run

```bash
python test_hb_modules.py
```

### What Happens
- Loads the OpenAI API key and initializes the GPT client.
- Sets up a sample image, category, question, and expectation.
- Builds a category-specific prompt and enhances it for AI validation.
- Validates the image (checks for blank/dark and compliance via AI).
- If validation passes, performs a full AI analysis (compliance, score, suggestions, and all fields).
- Prints detailed logs and results for each step.

**Tip:**
- You can modify the image path, category, question, or expectation at the top of `test_hb_modules.py` to test different scenarios.
- If the image fails validation (e.g., is blank or irrelevant), the pipeline will stop and print the reason.

---

## 📂 Dependencies

- Python 3.7+
- `openai`
- `Pillow`
- `numpy`

---

## 🔐 Security & API Keys

- Store the OpenAI API key in `openai_api_key.txt` or set it in the environment variable `OPENAI_API_KEY`.

---

## 👤 Authors

- **System Logic:** Vedant Deshmukh
- **Prompt Engineering:** GPT-4o based enhancement logic

---

## 📊 Future Enhancements

- Multi-language support
- Model selection (Claude, Gemini)
- Feedback loop for model fine-tuning

---


