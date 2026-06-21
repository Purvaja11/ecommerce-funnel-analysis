import pandas as pd
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, 'data')

orders = pd.read_csv(os.path.join(data_dir, 'orders_clean.csv'))
items = pd.read_csv(os.path.join(data_dir, 'items_clean.csv'))
products = pd.read_csv(os.path.join(data_dir, 'products_clean.csv'))
customers = pd.read_csv(os.path.join(data_dir, 'customers_clean.csv'))

# Merge into one flat table for Excel pivots
merged = items.merge(orders[['order_id','order_status','delivery_days','is_late','year_month']], on='order_id')
merged = merged.merge(products[['product_id','category_english']], on='product_id')
merged = merged.merge(orders[['order_id','customer_id']], on='order_id')
merged = merged.merge(customers[['customer_id','customer_state']], on='customer_id')

merged[['order_id','category_english','customer_state','price',
        'freight_value','delivery_days','is_late','year_month',
        'order_status']].to_csv(os.path.join(data_dir, 'excel_data.csv'), index=False)
print(f"✅ Excel data: {len(merged):,} rows saved")