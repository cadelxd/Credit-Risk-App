# Credit Risk Analyzer

A web application that allows users to upload Indian bank statement PDFs and uses the Gemini API to extract financial insights like average monthly inflow, outflow, and balance. These values are then passed to a trained XGBoost model to predict whether the user is high risk or low risk.

---

## How to Run

### 1. Clone the Repository
git clone https://github.com/cadelxd/Credit-Risk-App.git<br>
cd Credit-Risk-App<br>

### 2. Create and Activate Virtual Environment
python -m venv venv<br>
venv\Scripts\activate<br>

### 3. Install Dependencies
pip install -r requirements.txt

### 4. Set your Gemini API Key
create a .env file in the root directory:<br>
GEMINI_API_KEY=your_gemini_api_key_here

### 5. Apply Migrations
python manage.py makemigrations<br>
python manage.py migrate

### 6. Run the Development Server
python manage.py runserver

### 7. Access the App
visit: http://localhost:8000