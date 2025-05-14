import os
import pandas as pd

# Create mock_sharepoint folder
mock_folder = '/Users/arnavmenon/Code/extra/flexify/mock_sharepoint'
faq_path = os.path.join(mock_folder, 'faq.csv')
# os.makedirs(mock_folder, exist_ok=True)

# Load existing data
parts = pd.read_excel(os.path.join(mock_folder, 'part_list.xlsx'), sheet_name='Parts')
suppliers = pd.read_excel(os.path.join(mock_folder, 'suppliers.xlsx'), sheet_name='Suppliers')
orders = pd.read_excel(os.path.join(mock_folder, 'purchase_orders.xlsx'), sheet_name='Orders')

# Generate dynamic Q&A
qa_list = []

# 1. Average unit price by category
for category in parts['category'].unique():
    avg_price = parts.loc[parts['category'] == category, 'unit_price'].mean()
    qa_list.append({
        'question': f'What is the average unit price for {category} parts?',
        'answer': f'${avg_price:.2f}'
    })

# 2. Supplier with most orders
supplier_counts = orders['supplier_id'].value_counts()
top_supplier_id = supplier_counts.idxmax()
top_supplier_name = suppliers.loc[suppliers['supplier_id'] == top_supplier_id, 'supplier_name'].values[0]
qa_list.append({
    'question': 'Which supplier has the most purchase orders overall?',
    'answer': top_supplier_name
})

# 3. Number of orders per supplier (top 5)
top5 = supplier_counts.head(5)
for sup_id, count in top5.items():
    sup_name = suppliers.loc[suppliers['supplier_id'] == sup_id, 'supplier_name'].values[0]
    qa_list.append({
        'question': f'How many orders did {sup_name} place?',
        'answer': str(int(count))
    })

# 4. Total quantity per month (aggregate)
orders['order_month'] = pd.to_datetime(orders['order_date']).dt.to_period('M')
monthly_totals = orders.groupby('order_month')['quantity'].sum().head(6)
for period, total in monthly_totals.items():
    qa_list.append({
        'question': f'What was the total quantity ordered in {period}?',
        'answer': str(int(total))
    })

# 5. Part with highest unit price
max_price = parts['unit_price'].max()
max_part = parts.loc[parts['unit_price'] == max_price, 'part_name'].iloc[0]
qa_list.append({
    'question': 'Which part has the highest unit price?',
    'answer': max_part
})

# 6. Top 5 most ordered parts
part_counts = orders['part_id'].value_counts().head(5)
for pid, count in part_counts.items():
    pname = parts.loc[parts['part_id'] == pid, 'part_name'].values[0]
    qa_list.append({
        'question': f'How many times was {pname} ordered?',
        'answer': str(int(count))
    })

# 7. Average quantity per order
avg_qty = orders['quantity'].mean()
qa_list.append({
    'question': 'What is the average quantity per purchase order?',
    'answer': f'{avg_qty:.1f}'
})

# 8. Distinct parts and suppliers counts
qa_list.append({
    'question': 'How many distinct parts are there total?',
    'answer': str(parts['part_id'].nunique())
})
qa_list.append({
    'question': 'How many distinct suppliers are there total?',
    'answer': str(suppliers['supplier_id'].nunique())
})

# 9. Earliest and latest order dates
earliest = orders['order_date'].min()
latest = orders['order_date'].max()
qa_list.append({
    'question': 'What is the earliest order date in the dataset?',
    'answer': earliest
})
qa_list.append({
    'question': 'What is the latest order date in the dataset?',
    'answer': latest
})

# 10. Orders per category (by joining parts)
merged = orders.merge(parts[['part_id', 'category']], on='part_id')
cat_counts = merged['category'].value_counts()
for cat, cnt in cat_counts.items():
    qa_list.append({
        'question': f'How many orders include {cat} parts?',
        'answer': str(int(cnt))
    })

# 11. Supplier country distribution (top 3)
country_counts = suppliers['country'].value_counts().head(3)
for country, cnt in country_counts.items():
    qa_list.append({
        'question': f'How many suppliers are located in {country}?',
        'answer': str(int(cnt))
    })

# 12. Largest single order details
max_order = orders.loc[orders['quantity'].idxmax()]
sup_name = suppliers.loc[suppliers['supplier_id'] == max_order['supplier_id'], 'supplier_name'].values[0]
pname = parts.loc[parts['part_id'] == max_order['part_id'], 'part_name'].values[0]
qa_list.append({
    'question': 'What was the largest single order’s part, supplier, and quantity?',
    'answer': f'{pname} supplied by {sup_name} with quantity {int(max_order["quantity"])}'
})

# 13. Recent orders count (last 30 days of data range)
orders['order_date_dt'] = pd.to_datetime(orders['order_date'])
cutoff = orders['order_date_dt'].max() - pd.Timedelta(days=30)
recent_count = (orders['order_date_dt'] >= cutoff).sum()
qa_list.append({
    'question': 'How many orders were placed in the most recent 30-day period?',
    'answer': str(int(recent_count))
})

# 14. Price statistics (min, max, median) across all parts
qa_list.append({
    'question': 'What is the minimum, maximum, and median unit price across all parts?',
    'answer': f'Min: ${parts["unit_price"].min():.2f}, Max: ${parts["unit_price"].max():.2f}, Median: ${parts["unit_price"].median():.2f}'
})

# 15. Sample specific lookups
qa_list.append({
    'question': f'What is the contact email for {suppliers["supplier_name"].iloc[0]}?',
    'answer': suppliers["contact_email"].iloc[0]
})
qa_list.append({
    'question': f'What category is {parts["part_name"].iloc[10]}?',
    'answer': parts["category"].iloc[10]
})
qa_list.append({
    'question': f'How many orders reference {parts["part_name"].iloc[20]}?',
    'answer': str((orders['part_id'] == parts["part_id"].iloc[20]).sum())
})

# Save expanded FAQ
faq_df = pd.DataFrame(qa_list)
faq_df.to_csv(faq_path, index=False)