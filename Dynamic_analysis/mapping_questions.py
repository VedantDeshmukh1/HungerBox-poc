import pandas as pd
import openai
import os
import streamlit as st

# Use st.secrets for OpenAI API key
openai.api_key = st.secrets["openai"]["api_key"]

def categorize_questions(questions_df):
    # Create categories list
    categories = [
        "Hygiene & Cleanliness",
        "Inventory & Storage",
        "Food Safety Compliance",
        "Hardware (Assets) & Other Equipment",
        "Marketing"
    ]
    
    # Create an empty list to store categorization results
    all_categorizations = []
    questions_df = questions_df.drop_duplicates(subset=['questions'])
    
    # Iterate through each question
    for index, row in questions_df.iterrows():
        question = row['questions']
        
        # Skip empty questions
        if pd.isna(question) or question.strip() == '':
            all_categorizations.append('')
            continue
        
        # Create prompt for OpenAI
        prompt = f"""
        Categorize the following question into one or more of these categories. 
        Return only the categories separated by commas, without any other text.
        
        Question: "{question}"
        
        Categories:
        - Hygiene & Cleanliness
        - Inventory & Storage
        - Food Safety Compliance
        - Hardware (Assets) & Other Equipment
        - Marketing
        
        Output format should be only the category names separated by commas, for example: "Hygiene & Cleanliness, Food Safety Compliance"
        """
        
        # Call OpenAI API
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that categorizes questions about food service operations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            # Extract categorization
            categorization = response.choices[0].message.content.strip()
            
            # Format categorization with square brackets
            categories_list = [cat.strip() for cat in categorization.split(',')]
            formatted_categorization = f"[{', '.join(categories_list)}]"
            
            all_categorizations.append(formatted_categorization)
            
            # Print progress
            print(f"Processed question {index+1}: {formatted_categorization}")
            
        except Exception as e:
            print(f"Error processing question {index+1}: {e}")
            all_categorizations.append("Error")
    
    # Add categorizations to the dataframe
    questions_df['categorization'] = all_categorizations
    
    return questions_df

def main():
    # Load the questions CSV file
    input_file = "IBM Checklist Data with cleaned questions.xlsx - Sheet2.csv"
    try:
        questions_df = pd.read_csv(input_file)
        #questions_df = questions_df.head(650)
    except Exception as e:
        print(f"Error loading file: {e}")
        # Try different encoding if initial load fails
        try:
            questions_df = pd.read_csv(input_file, encoding='latin1')
        except Exception as e:
            print(f"Error loading file with alternative encoding: {e}")
            return
        
    # Rename 'question' column to 'questions' if it exists
    if 'question' in questions_df.columns:
        questions_df = questions_df.rename(columns={'question': 'questions'})
    
    # Check if 'questions' column exists
    if 'questions' not in questions_df.columns:
        print(f"Column 'questions' not found. Available columns: {questions_df.columns.tolist()}")
        return
    
    # Process the questions
    categorized_df = categorize_questions(questions_df)
    
    # Save the result
    output_file = "categorized_questions.csv"
    categorized_df.to_csv(output_file, index=False)
    print(f"Categorized questions saved to {output_file}")
    categorized_df = pd.read_csv("categorized_questions.csv")
    
    # Now handle the full CSV file if it's provided
    csv_file = input("Enter the path to the CSV file (or press Enter to skip): ")
    if csv_file and csv_file.strip():
        try:
            # Load the xlsx file
            full_df = pd.read_excel(csv_file)
            
            # Check if the question column exists in the CSV file
            question_col = None
            for col in full_df.columns:
                if "question" in col.lower():
                    question_col = col
                    break
            
            if not question_col:
                print("Could not find question column in CSV file")
                return
            
            # Create a mapping from questions to categories
            question_to_category = dict(zip(categorized_df['questions'], categorized_df['categorization']))
            
            # Apply the mapping to the CSV file
            def get_category(question):
                return question_to_category.get(question, "")
            
            full_df['categorization'] = full_df[question_col].apply(get_category)
            
            # Save the updated CSV file
            output_csv = "categorized_" + os.path.basename(csv_file)
            full_df.to_csv(output_csv, index=False)
            print(f"Updated CSV file saved to {output_csv}")
            
        except Exception as e:
            print(f"Error processing CSV file: {e}")

if __name__ == "__main__":
    main()