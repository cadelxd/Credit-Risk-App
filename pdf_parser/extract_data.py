import os
import base64
import google.generativeai as genai
import json
import re
from dotenv import load_dotenv

load_dotenv()

# Init Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def convert_pdf_to_base64(pdf_path):
    with open(pdf_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def extract_statement_data(pdf_path):
    img_data = convert_pdf_to_base64(pdf_path)
    
    prompt = """
You are a financial assistant. The user has uploaded a **multi-page Indian bank statement in PDF format**.

- Extract the following summary information only:
  - "avg_monthly_inflow"
  - "avg_monthly_outflow"
  - "avg_monthly_balance"
  
- Return a **JSON object** with only these 3 keys and float values in rupees.
- Do not return any extra commentary or markdown.
"""

    response = model.generate_content([
        prompt,
        {"mime_type": "application/pdf", "data": img_data}
    ])
    
    raw_text = response.text.strip()
    raw_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.DOTALL).strip()

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parsing failed: {e}\nResponse text was:\n{raw_text}")

    if not all(key in data for key in ['avg_monthly_inflow', 'avg_monthly_outflow', 'avg_monthly_balance']):
        raise ValueError("Missing expected average keys in Gemini output.")

    return data
