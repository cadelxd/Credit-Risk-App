import glob
import os
import pandas as pd
import joblib

model = joblib.load('data/model/xgb_credit_risk_model.joblib')

folder_path = 'data/extracted_csv/'

rename_map = {
    'average_monthly_balance': 'avg_balance',
    'average_monthly_inflows': 'monthly_inflows',
    'average_monthly_outflows': 'monthly_outflows'
}

class_map = {0: 'low risk', 1: 'high risk'}

csv_files = glob.glob(os.path.join(folder_path, '*.csv'))

for csv_file in csv_files:
    df = pd.read_csv(csv_file)
    
    df.rename(columns=rename_map, inplace=True)
    
    features = ['avg_balance', 'monthly_inflows', 'monthly_outflows']
    
    if all(f in df.columns for f in features):
        X = df[features]
        
        prediction = model.predict(X)[0]
        
        print(f"prediction for {os.path.basename(csv_file)} is {class_map[prediction]}")
    else:
        missing = [f for f in features if f not in df.columns]
        print(f"Skipping {os.path.basename(csv_file)} due to missing features: {missing}")
