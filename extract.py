import os
import pandas as pd
from pdf_parser.extract_data import extract_statement_data

RAW_PDF_DIR = "data/raw_pdfs"
OUTPUT_CSV_DIR = "data/extracted_csv"
os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)

def process_pdf(pdf_path):
    print(f"\nProcessing {os.path.basename(pdf_path)} ...")
    try:
        summary = extract_statement_data(pdf_path)

        summary_df = pd.DataFrame([{
            'avg_balance': summary['avg_monthly_balance'],
            'monthly_inflows': summary['avg_monthly_inflow'],
            'monthly_outflows': summary['avg_monthly_outflow']
        }])

        output_csv_path = os.path.join(
            OUTPUT_CSV_DIR,
            os.path.splitext(os.path.basename(pdf_path))[0] + ".csv"
        )
        summary_df.to_csv(output_csv_path, index=False)

        print("Success")
    except Exception as e:
        print(f"Failed {os.path.basename(pdf_path)}: {e}")

if __name__ == "__main__":
    for filename in os.listdir(RAW_PDF_DIR):
        if filename.lower().endswith(".pdf"):
            process_pdf(os.path.join(RAW_PDF_DIR, filename))
