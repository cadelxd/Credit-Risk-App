import os
import tempfile
import pandas as pd
import joblib
from django.shortcuts import render, redirect
from .forms import PDFUploadForm, UserRegistrationForm
from extract import extract_statement_data
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Risk bucket utility
def risk_bucket(score):
    if score < 30:
        return "Low Risk"
    elif score < 70:
        return "Medium Risk"
    else:
        return "High Risk"

# Registration view
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

# Credit risk explanation logic
def explain_credit_risk(features):
    explanations = []
    if features.get('credit_utilization_ratio', 0) > 0.8:
        explanations.append("Credit utilization ratio is very high.")
    if features.get('late_fee_ratio', 0) > 0.1:
        explanations.append("Frequent late fees detected.")
    if features.get('total_outstanding_balance', 0) > features.get('credit_limit', 0):
        explanations.append("Outstanding balance exceeds the credit limit.")
    if features.get('repayment_ratio', 1) < 0.5:
        explanations.append("Repayment ratio is low, indicating potential repayment issues.")
    return explanations

# Debit risk explanation logic
def explain_debit_risk(features):
    explanations = []
    if features.get('bounce_rate', 0) > 0.05:
        explanations.append("High rate of bounced transactions.")
    if features.get('spending_to_income_ratio', 0) > 0.9:
        explanations.append("Spending is too close to or exceeds income.")
    if features.get('emi_to_income_ratio', 0) > 0.3:
        explanations.append("EMI payments consume a large portion of income.")
    return explanations

# Main home/upload view
@login_required
def home(request):
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        uploaded_files = request.FILES.getlist('pdf_file')
        group_by = request.POST.get('group_by', 'overall')
        summaries = []

        if uploaded_files:
            for uploaded_file in uploaded_files:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                        for chunk in uploaded_file.chunks():
                            temp_pdf.write(chunk)
                        temp_pdf_path = temp_pdf.name

                    summary = extract_statement_data(temp_pdf_path)
                    os.remove(temp_pdf_path)

                    if 'account_type' not in summary:
                        return render(request, 'CreditRiskApp/result.html', {
                            'prediction': f"⚠️ Could not extract valid data from {uploaded_file.name}."
                        })

                    summary['source'] = uploaded_file.name  # Track source filename for grouping
                    summaries.append(summary)

                except Exception as e:
                    return render(request, 'CreditRiskApp/result.html', {
                        'prediction': f"⚠️ Error processing {uploaded_file.name}: {str(e)}"
                    })

        if not summaries:
            return render(request, 'CreditRiskApp/upload.html', {
                'form': form,
                'error': "Please upload at least one valid bank statement PDF."
            })

        if group_by == 'name':
            # Group by extracted name (not filename)
            grouped = {}
            for summary in summaries:
                name = summary.get('name', 'Unknown')
                grouped.setdefault(name, []).append(summary)

            results = []
            for name, group_summaries in grouped.items():
                result = calculate_risk(group_summaries, name=name)
                results.append(result)

            return render(request, 'CreditRiskApp/result.html', {
                'grouped_results': results,
                'used_upload': True,
                'grouped_by': 'name'
            })

        else:
            # Overall aggregation
            result = calculate_risk(summaries)
            return render(request, 'CreditRiskApp/result.html', {
                'overall_result': result,
                'overall_explanations': result['explanations'],
                'used_upload': True,
                'grouped_by': 'overall'
            })

    else:
        form = PDFUploadForm()
        return render(request, 'CreditRiskApp/upload.html', {'form': form})


def calculate_risk(summaries, name=None):
    credit_summaries = [s for s in summaries if s.get('account_type') == 'credit']
    debit_summaries = [s for s in summaries if s.get('account_type') == 'debit']

    credit_risk_score = 0
    debit_risk_score = 0
    explanations_credit = []
    explanations_debit = []

    if credit_summaries:
        df_credit = pd.DataFrame(credit_summaries)
        credit_aggregated = {
            'credit_limit': df_credit['credit_limit'].mean(),
            'total_outstanding_balance': df_credit['total_outstanding_balance'].mean(),
            'credit_utilization_ratio': df_credit['credit_utilization_ratio'].mean(),
            'repayment_ratio': df_credit['repayment_ratio'].mean(),
            'late_fee_ratio': df_credit['late_fee_ratio'].mean()
        }
        model_credit = joblib.load('data/model/credit_model.joblib')
        credit_risk_score = model_credit.predict(pd.DataFrame([credit_aggregated]))[0]
        explanations_credit = explain_credit_risk(credit_aggregated)

    if debit_summaries:
        df_debit = pd.DataFrame(debit_summaries)
        debit_aggregated = {
            'avg_monthly_inflow': df_debit['avg_monthly_inflow'].mean(),
            'avg_closing_balance': df_debit['avg_closing_balance'].mean(),
            'spending_to_income_ratio': df_debit['spending_to_income_ratio'].mean(),
            'emi_to_income_ratio': df_debit['emi_to_income_ratio'].mean(),
            'bounce_rate': df_debit['bounce_rate'].mean()
        }
        model_debit = joblib.load('data/model/debit_model.joblib')
        debit_risk_score = model_debit.predict(pd.DataFrame([debit_aggregated]))[0]
        explanations_debit = explain_debit_risk(debit_aggregated)

    overall_risk_score = max(credit_risk_score, debit_risk_score)
    all_explanations = explanations_credit + explanations_debit

    return {
        'name': name,
        'account_type': 'Grouped' if name else 'Overall',
        'risk_score': round(overall_risk_score, 2),
        'prediction': risk_bucket(overall_risk_score),
        'aggregated': None,
        'explanations': all_explanations
    }
