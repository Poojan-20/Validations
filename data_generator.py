import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set seed for reproducibility
np.random.seed(42)

# Generate sample data
def generate_sample_data(num_records=100):
    # Create transaction IDs
    txn_ids = [f"TXN{i:06d}" for i in range(1, num_records + 1)]
    
    # Create base date and generate dates over a 30-day period
    base_date = datetime(2023, 1, 1)
    dates = [(base_date + timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d') for _ in range(num_records)]
    
    # Generate status values
    statuses = np.random.choice(['Approved', 'Pending', 'Rejected', 'In Review'], size=num_records)
    
    # Generate sale amounts (between 100 and 1000)
    sale_amounts = np.random.uniform(100, 1000, num_records).round(2)
    
    # Generate revenue based on sale amount (typically a percentage)
    base_revenue = sale_amounts * np.random.uniform(0.1, 0.3, num_records).round(2)
    
    # Generate brand names
    brands = np.random.choice(['Nike', 'Adidas', 'Puma', 'Reebok', 'Under Armour', 'New Balance'], size=num_records)
    
    # Create client dataframe
    client_data = pd.DataFrame({
        'txn_id': txn_ids,
        'status': statuses,
        'sale_amount': sale_amounts,
        'revenue': base_revenue,
        'brand_name': brands,
        'date': dates
    })
    
    # Create Trackier dataframe (with some differences to test all use cases)
    trackier_data = client_data.copy()
    
    # Create test cases for each validation scenario
    # We'll modify a subset of records for each case

    # Use indices to ensure non-overlapping modifications for test cases
    indices = list(range(num_records))
    np.random.shuffle(indices)
    
    # Allocate indices for each use case (10 records per use case)
    records_per_case = 10
    case_indices = [indices[i:i+records_per_case] for i in range(0, min(80, num_records), records_per_case)]
    
    if len(case_indices) >= 8:
        # Case 1 (perfect match): no changes needed
        
        # Case 2: Status matching, Sale amount matching, Revenue mis-matching
        for idx in case_indices[1]:
            trackier_data.loc[idx, 'revenue'] = client_data.loc[idx, 'revenue'] * np.random.uniform(0.8, 1.2)
            
        # Case 3: Status matching, Sale amount mis-matching, Revenue matching
        for idx in case_indices[2]:
            original_sale = client_data.loc[idx, 'sale_amount']
            original_revenue = client_data.loc[idx, 'revenue']
            rate = original_revenue / original_sale
            new_sale = original_sale * np.random.uniform(0.8, 1.2)
            trackier_data.loc[idx, 'sale_amount'] = new_sale
            # Adjust revenue to maintain the same rate
            trackier_data.loc[idx, 'revenue'] = rate * new_sale
            
        # Case 4: Status matching, Sale amount mis-matching, Revenue mis-matching
        for idx in case_indices[3]:
            trackier_data.loc[idx, 'sale_amount'] = client_data.loc[idx, 'sale_amount'] * np.random.uniform(0.8, 1.2)
            trackier_data.loc[idx, 'revenue'] = client_data.loc[idx, 'revenue'] * np.random.uniform(0.8, 1.2)
            
        # Case 5: Status mis-matching, Sale amount matching, Revenue matching
        for idx in case_indices[4]:
            current_status = client_data.loc[idx, 'status']
            new_status = current_status
            while new_status == current_status:
                new_status = np.random.choice(['Approved', 'Pending', 'Rejected', 'In Review'])
            trackier_data.loc[idx, 'status'] = new_status
            
        # Case 6: Status mis-matching, Sale amount matching, Revenue mis-matching
        for idx in case_indices[5]:
            current_status = client_data.loc[idx, 'status']
            new_status = current_status
            while new_status == current_status:
                new_status = np.random.choice(['Approved', 'Pending', 'Rejected', 'In Review'])
            trackier_data.loc[idx, 'status'] = new_status
            trackier_data.loc[idx, 'revenue'] = client_data.loc[idx, 'revenue'] * np.random.uniform(0.8, 1.2)
            
        # Case 7: Status mis-matching, Sale amount mis-matching, Revenue matching
        for idx in case_indices[6]:
            current_status = client_data.loc[idx, 'status']
            new_status = current_status
            while new_status == current_status:
                new_status = np.random.choice(['Approved', 'Pending', 'Rejected', 'In Review'])
            trackier_data.loc[idx, 'status'] = new_status
            
            original_sale = client_data.loc[idx, 'sale_amount']
            original_revenue = client_data.loc[idx, 'revenue']
            rate = original_revenue / original_sale
            new_sale = original_sale * np.random.uniform(0.8, 1.2)
            trackier_data.loc[idx, 'sale_amount'] = new_sale
            # Adjust revenue to maintain the same rate
            trackier_data.loc[idx, 'revenue'] = rate * new_sale
            
        # Case 8: Status mis-matching, Sale amount mis-matching, Revenue mis-matching
        for idx in case_indices[7]:
            current_status = client_data.loc[idx, 'status']
            new_status = current_status
            while new_status == current_status:
                new_status = np.random.choice(['Approved', 'Pending', 'Rejected', 'In Review'])
            trackier_data.loc[idx, 'status'] = new_status
            trackier_data.loc[idx, 'sale_amount'] = client_data.loc[idx, 'sale_amount'] * np.random.uniform(0.8, 1.2)
            trackier_data.loc[idx, 'revenue'] = client_data.loc[idx, 'revenue'] * np.random.uniform(0.8, 1.2)
    
    # Add/remove some transactions to test missing transactions case
    if num_records >= 90:
        # Add 5 transactions only in client data
        client_only_txn_ids = [f"CLNT{i:06d}" for i in range(1, 6)]
        client_only_data = pd.DataFrame({
            'txn_id': client_only_txn_ids,
            'status': np.random.choice(['Approved', 'Pending', 'Rejected', 'In Review'], size=5),
            'sale_amount': np.random.uniform(100, 1000, 5).round(2),
            'revenue': np.random.uniform(10, 200, 5).round(2),
            'brand_name': np.random.choice(['Nike', 'Adidas', 'Puma', 'Reebok', 'Under Armour', 'New Balance'], size=5),
            'date': [(base_date + timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d') for _ in range(5)]
        })
        client_data = pd.concat([client_data, client_only_data], ignore_index=True)
        
        # Add 5 transactions only in trackier data
        trackier_only_txn_ids = [f"TRKR{i:06d}" for i in range(1, 6)]
        trackier_only_data = pd.DataFrame({
            'txn_id': trackier_only_txn_ids,
            'status': np.random.choice(['Approved', 'Pending', 'Rejected', 'In Review'], size=5),
            'sale_amount': np.random.uniform(100, 1000, 5).round(2),
            'revenue': np.random.uniform(10, 200, 5).round(2),
            'brand_name': np.random.choice(['Nike', 'Adidas', 'Puma', 'Reebok', 'Under Armour', 'New Balance'], size=5),
            'date': [(base_date + timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d') for _ in range(5)]
        })
        trackier_data = pd.concat([trackier_data, trackier_only_data], ignore_index=True)
    
    return client_data, trackier_data

# Generate sample data
client_data, trackier_data = generate_sample_data(100)

# Save to Excel files
client_data.to_excel('client_data_sample.xlsx', index=False)
trackier_data.to_excel('trackier_data_sample.xlsx', index=False)

print("Sample data files created:")
print("1. client_data_sample.xlsx")
print("2. trackier_data_sample.xlsx")

# Display summary of test cases
print("\nTest case summary:")
print(f"Total records: {len(client_data)}")
print("- Each use case has approximately 10 test records")
print("- 5 transactions only in client data")
print("- 5 transactions only in trackier data")