import os
import json
from pdf_parser.extract_data import extract_statement_data

RAW_PDF_DIR = "data/raw_pdfs"
OUTPUT_JSON_PATH = "data/extracted_csv/combined_output.json"

def process_all_pdfs():
    combined_data = []

    for filename in os.listdir(RAW_PDF_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(RAW_PDF_DIR, filename)
            print(f"\nProcessing {filename} ...")

            try:
                summary = extract_statement_data(pdf_path)

                combined_data.append({
                    'filename': filename,
                    'avg_monthly_balance': summary['avg_monthly_balance'],
                    'avg_monthly_inflow': summary['avg_monthly_inflow'],
                    'avg_monthly_outflow': summary['avg_monthly_outflow']
                })

                print("Success")

            except Exception as e:
                print(f"Failed {filename}: {e}")

    return combined_data

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
    results = process_all_pdfs()

    # Save to JSON file
    with open(OUTPUT_JSON_PATH, 'w') as json_file:
        json.dump(results, json_file, indent=4)

    print(f"\nAll results saved to {OUTPUT_JSON_PATH}")
