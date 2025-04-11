# 🍽️ HungerBox Restaurant Compliance Analysis Dashboard

This Streamlit application provides a comprehensive dashboard to analyze restaurant compliance based on inspection data. It helps identify compliance trends, critical issues, and improvement areas across various restaurants under the HungerBox ecosystem.

## 🚀 Features

- **Overview Dashboard**:
  - Pie chart for overall compliance status
  - Bar chart showing severity level distribution
  - Visualization of common image quality issues
  - Most frequent tags across inspections
  - Compliance trend over time

- **Restaurant-Specific Analysis**:
  - Select individual restaurants for deep dive
  - Compliance percentage and critical issue counts
  - Restaurant-specific image quality and tag analysis
  - View of non-compliant inspection records with suggestions

- **Individual Records Viewer**:
  - Powerful filtering by restaurant, compliance status, severity, and image quality
  - Tabular view of individual inspection records

## 📊 Data Format

The application expects an Excel file with inspection data in the following format:

| Column Name             | Description                                             |
|-------------------------|---------------------------------------------------------|
| `cafeteria name`        | Name of the restaurant/cafeteria                        |
| `compliance_status`     | Whether the inspection is compliant (`Yes`/`No`)        |
| `severity_level`        | Severity of the issue (`Critical`, `Moderate`, etc.)   |
| `tags`                  | Tags related to the inspection                          |
| `image_quality_issues`  | Issues found with the image (`too_dark`, `blurry`, etc.)|
| `analysis_date`         | Date of inspection                                      |
| `question`              | Inspection question                                     |
| `explanation`           | Explanation for non-compliance                          |
| `improvement_suggestions`| Suggestions for improvement                             |

> 🔁 Some columns are optional. The app dynamically adapts to the available data.

## 📁 File Setup

Place your Excel file in the project directory and rename it (or update the path in the code):

```python
EXCEL_FILE_PATH = "analysis_results_20250407_221405.xlsx"
```

## 💻 How to Run

1. **Install dependencies**:

```bash
pip install streamlit pandas numpy matplotlib seaborn plotly pillow openpyxl requests
```

2. **Set up secrets**:
   - Create a `.streamlit/secrets.toml` file with the following content:

   ```toml
   [openai]
   api_key = "your-openai-api-key"

   [supabase]
   url = "your-supabase-url"
   key = "your-supabase-key"
   ```

3. **Run the Streamlit app**:

```bash
streamlit run vision_analysis_app.py
```

4. **Open the browser** at the given URL (usually `http://localhost:8501`).

## 📷 Image Loading

The app attempts to display images via URLs found in the `upload_links (images)` column. Ensure image URLs are accessible and properly formatted (JSON list or direct URL).

## 🙌 Contributions

Feel free to fork the repo and enhance the dashboard — whether by improving visuals, adding export features, or connecting a database.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.