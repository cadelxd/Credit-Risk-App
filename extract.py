import os
import base64
import google.generativeai as genai
import json
import re
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def convert_pdf_to_base64(pdf_path):
    with open(pdf_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def clean_response_text(raw_text):
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.DOTALL).strip()

def detect_account_type(pdf_path):
    img_data = convert_pdf_to_base64(pdf_path)

    detection_prompt = """
You are a document classifier. The user has uploaded a multi-page Indian bank statement in PDF format.

Identify if it is a **debit account (like savings or current)** or a **credit card account**.

Respond with only one word: "debit" or "credit"
"""

    response = model.generate_content([
        detection_prompt,
        {"mime_type": "application/pdf", "data": img_data}
    ])

    account_type = response.text.strip().lower()
    if account_type not in ["debit", "credit"]:
        raise ValueError(f"Failed to classify account type. Got: {account_type}")
    
    return account_type

def extract_statement_data(pdf_path):
    img_data = convert_pdf_to_base64(pdf_path)
    account_type = detect_account_type(pdf_path)

    if account_type == "debit":
        prompt = """
You are a financial assistant. The user has uploaded an Indian **debit account** bank statement PDF.

Extract the following features:
-"name" (account holder's name)
- "avg_monthly_inflow"
- "avg_closing_balance"
- "spending_to_income_ratio"
- "emi_to_income_ratio"
- "bounce_rate"

If any feature is missing or not explicitly stated, infer or estimate it based on the available data. Convert to INR wherever applicable. 

Return a JSON object with only these keys and float values. No explanation or markdown.
"""
    else:  # credit
        prompt = """
You are a financial assistant. The user has uploaded an Indian **credit card account** statement PDF.

Extract the following features:
-"name" (account holder's name)
- "credit_limit"
- "total_outstanding_balance"
- "credit_utilization_ratio"
- "repayment_ratio"
- "late_fee_ratio"

If any feature is missing or not explicitly stated, infer or estimate it based on the available data. Convert to INR wherever applicable.

Return a JSON object with only these keys and float values. No explanation or markdown.
"""

    response = model.generate_content([
        prompt,
        {"mime_type": "application/pdf", "data": img_data}
    ])

    raw_text = clean_response_text(response.text)
    
    try:
        features = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parsing failed: {e}\nResponse was:\n{raw_text}")

    # Return a flat dict with account_type and features merged
    result = {"account_type": account_type}
    result.update(features)
    return result
