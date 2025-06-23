import os
import tempfile
import pandas as pd
from django.shortcuts import render, redirect
from .forms import PDFUploadForm, UserRegistrationForm
from extract import extract_statement_data
import joblib
from django.contrib import messages
from django.contrib.auth.decorators import login_required

class_map = {0: 'Low Risk', 1: 'High Risk'}

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. You can now log in.")
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'CreditRiskApp/register.html', {'form': form})

@login_required
def home(request):
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['pdf_file']

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                for chunk in uploaded_file.chunks():
                    temp_pdf.write(chunk)
                temp_pdf_path = temp_pdf.name

            try:
                data = extract_statement_data(temp_pdf_path)

                renamed = {
                    'avg_balance': data['avg_monthly_balance'],
                    'monthly_inflows': data['avg_monthly_inflow'],
                    'monthly_outflows': data['avg_monthly_outflow']
                }
                model = joblib.load('data/model/xgb_credit_risk_model.joblib')
                df = pd.DataFrame([renamed])
                result = model.predict(df)[0]
                prediction = class_map[result]

                os.remove(temp_pdf_path)

                return render(request, 'CreditRiskApp/result.html', {
                    'prediction': prediction
                })

            except Exception as e:
                prediction = f"Error: {str(e)}"
                return render(request, 'CreditRiskApp/result.html', {
                    'prediction': prediction
                })
    else:
        form = PDFUploadForm()

    return render(request, 'CreditRiskApp/upload.html', {'form': form})
