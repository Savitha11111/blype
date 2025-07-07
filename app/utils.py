# app/utils.py

import pandas as pd

def parse_uploaded_file(file):
    try:
        if file.name.endswith(".csv"):
            return pd.read_csv(file)
        elif file.name.endswith(".xlsx"):
            return pd.read_excel(file)
        else:
            return None
    except Exception as e:
        print(f"Error parsing file: {e}")
        return None
