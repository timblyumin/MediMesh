import pandas as pd
import numpy as np

def create_dataset():
    df = pd.DataFrame({
        'patient_id': range(1, 101),
        'acuity_level': np.random.randint(1, 6, 100),
        'department': np.random.choice(['ER', 'ICU', 'General'], 100)
    })
    df.to_csv('data/hospital_data.csv', index=False)
    print("Success: Synthetic data generated in data/hospital_data.csv")

if __name__ == "__main__":
    create_dataset()
