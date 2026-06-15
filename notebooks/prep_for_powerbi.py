import pandas as pd
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, 'data')

# ── Orders ─────────────────────────────────────────────
orders = pd.read_csv(os.path.join(data_dir, 'olist_orders_dataset.csv'))
orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])
orders['order_delivered_customer_date'] = pd.to_datetime(orders['order_delivered_customer_date'])
orders['order_estimated_delivery_date'] = pd.to_datetime(orders['order_estimated_delivery_date'])
orders['delivery_days'] = (orders['order_delivered_customer_date'] - 
                            orders['order_purchase_timestamp']).dt.days
orders['is_late'] = (orders['order_delivered_customer_date'] > 
                     orders['order_estimated_delivery_date']).astype(int)
orders['year_month'] = orders['order_purchase_timestamp'].dt.to_period('M').astype(str)
orders.to_csv(os.path.join(data_dir, 'orders_clean.csv'), index=False)
print(f"✅ Orders: {len(orders):,} rows")

# ── Order Items ────────────────────────────────────────
items = pd.read_csv(os.path.join(data_dir, 'olist_order_items_dataset.csv'))
items.to_csv(os.path.join(data_dir, 'items_clean.csv'), index=False)
print(f"✅ Items: {len(items):,} rows")

# ── Reviews ────────────────────────────────────────────
reviews = pd.read_csv(os.path.join(data_dir, 'olist_order_reviews_dataset.csv'))
# Keep only one review per order (some orders have duplicates — this causes the error)
reviews = reviews.drop_duplicates(subset='order_id', keep='first')
reviews.to_csv(os.path.join(data_dir, 'reviews_clean.csv'), index=False)
print(f"✅ Reviews: {len(reviews):,} rows")

# ── Customers ──────────────────────────────────────────
customers = pd.read_csv(os.path.join(data_dir, 'olist_customers_dataset.csv'))
customers.to_csv(os.path.join(data_dir, 'customers_clean.csv'), index=False)
print(f"✅ Customers: {len(customers):,} rows")

# ── Categories + Products merged ──────────────────────
products = pd.read_csv(os.path.join(data_dir, 'olist_products_dataset.csv'))
categories = pd.read_csv(os.path.join(data_dir, 'product_category_name_translation.csv'))
products = products.merge(categories, on='product_category_name', how='left')
products['category_english'] = products['product_category_name_english'].fillna(
    products['product_category_name']
)
products.to_csv(os.path.join(data_dir, 'products_clean.csv'), index=False)
print(f"✅ Products: {len(products):,} rows")

# ── Payments ───────────────────────────────────────────
payments = pd.read_csv(os.path.join(data_dir, 'olist_order_payments_dataset.csv'))
payments.to_csv(os.path.join(data_dir, 'payments_clean.csv'), index=False)
print(f"✅ Payments: {len(payments):,} rows")

# ── Sellers ────────────────────────────────────────────
sellers = pd.read_csv(os.path.join(data_dir, 'olist_sellers_dataset.csv'))
sellers.to_csv(os.path.join(data_dir, 'sellers_clean.csv'), index=False)
print(f"✅ Sellers: {len(sellers):,} rows")

# ── Late delivery by state and category ───────────────
late = orders[orders['is_late'] == 1].copy()
late = late.merge(
    pd.read_csv(os.path.join(data_dir, 'olist_customers_dataset.csv'))[
        ['customer_id','customer_state']],
    on='customer_id', how='left'
)
late.to_csv(os.path.join(data_dir, 'late_orders_clean.csv'), index=False)
print(f"✅ Late orders: {len(late):,} rows")

print("\n✅ All clean files saved — ready for Power BI")