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
        print("POST received")
        print("FILES:", request.FILES.getlist('pdf_file'))

        form = PDFUploadForm(request.POST, request.FILES)
        uploaded_files = request.FILES.getlist('pdf_file')
        summaries = []

        # --- Manual Inputs ---
        manual_data = {}
        try:
            avg_balance = request.POST.get('avg_balance')
            avg_inflow = request.POST.get('avg_inflow')
            avg_outflow = request.POST.get('avg_outflow')

            if avg_balance and avg_inflow and avg_outflow:
                manual_data = {
                    'avg_monthly_balance': float(avg_balance),
                    'avg_monthly_inflow': float(avg_inflow),
                    'avg_monthly_outflow': float(avg_outflow)
                }
        except ValueError:
            messages.error(request, "⚠️ Manual inputs must be valid numbers.")
            return render(request, 'CreditRiskApp/upload.html', {'form': form})

        # --- Process Uploaded PDFs ---
        if uploaded_files:
            for uploaded_file in uploaded_files:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                        for chunk in uploaded_file.chunks():
                            temp_pdf.write(chunk)
                        temp_pdf_path = temp_pdf.name

                    summary = extract_statement_data(temp_pdf_path)
                    summaries.append(summary)
                    os.remove(temp_pdf_path)

                except Exception as e:
                    return render(request, 'CreditRiskApp/result.html', {
                        'prediction': f"⚠️ Error processing {uploaded_file.name}: {str(e)}"
                    })

        # --- Combine Sources ---
        data_sources = []
        if manual_data:
            data_sources.append(manual_data)
        if summaries:
            data_sources.extend(summaries)

        if not data_sources:
            return render(request, 'CreditRiskApp/upload.html', {
                'form': form,
                'error': "Please provide either manual input, upload a valid PDF, or both."
            })

        # --- Aggregate Data ---
        df = pd.DataFrame(data_sources)
        aggregated = {
            'avg_balance': df['avg_monthly_balance'].mean(),
            'monthly_inflows': df['avg_monthly_inflow'].mean(),
            'monthly_outflows': df['avg_monthly_outflow'].mean()
        }

        # --- Predict with Model ---
        model = joblib.load('data/model/xgb_credit_risk_model.joblib')
        result = model.predict(pd.DataFrame([aggregated]))[0]
        prediction = class_map[result]

        return render(request, 'CreditRiskApp/result.html', {
            'prediction': prediction,
            'aggregated': aggregated,
            'used_manual': bool(manual_data),
            'used_upload': bool(summaries)
        })

    else:
        form = PDFUploadForm()
        return render(request, 'CreditRiskApp/upload.html', {'form': form})
