import sqlite3
import pandas as pd
import os

# ── Load all CSVs into SQLite ──────────────────────────
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, 'data')
db_path  = os.path.join(data_dir, 'olist.db')

conn = sqlite3.connect(db_path)

files = {
    'orders':       'olist_orders_dataset.csv',
    'customers':    'olist_customers_dataset.csv',
    'order_items':  'olist_order_items_dataset.csv',
    'payments':     'olist_order_payments_dataset.csv',
    'reviews':      'olist_order_reviews_dataset.csv',
    'products':     'olist_products_dataset.csv',
    'sellers':      'olist_sellers_dataset.csv',
    'categories':   'product_category_name_translation.csv',
}

print("Loading CSVs into SQLite...")
for table, filename in files.items():
    df = pd.read_csv(os.path.join(data_dir, filename))
    df.to_sql(table, conn, if_exists='replace', index=False)
    print(f"  ✅ {table}: {len(df):,} rows")

# ── Q1: Order Status Funnel ────────────────────────────
print("\n📊 Q1 — Order Status Funnel:")
q1 = pd.read_sql_query("""
    SELECT 
        order_status,
        COUNT(*) as order_count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM orders), 2) as pct
    FROM orders
    GROUP BY order_status
    ORDER BY order_count DESC
""", conn)
print(q1.to_string(index=False))

# ── Q2: Delivery Performance ───────────────────────────
print("\n📊 Q2 — Delivery Performance:")
q2 = pd.read_sql_query("""
    SELECT
        COUNT(*) as total_delivered,
        ROUND(AVG(JULIANDAY(order_delivered_customer_date) - 
              JULIANDAY(order_purchase_timestamp)), 1) as avg_delivery_days,
        ROUND(AVG(JULIANDAY(order_estimated_delivery_date) - 
              JULIANDAY(order_purchase_timestamp)), 1) as avg_estimated_days,
        SUM(CASE WHEN order_delivered_customer_date > order_estimated_delivery_date 
            THEN 1 ELSE 0 END) as late_deliveries,
        ROUND(SUM(CASE WHEN order_delivered_customer_date > order_estimated_delivery_date 
            THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as late_pct
    FROM orders
    WHERE order_status = 'delivered'
    AND order_delivered_customer_date IS NOT NULL
""", conn)
print(q2.to_string(index=False))

# ── Q3: Revenue by Category ────────────────────────────
print("\n📊 Q3 — Top 10 Categories by Revenue:")
q3 = pd.read_sql_query("""
    SELECT 
        COALESCE(ct.product_category_name_english, p.product_category_name, 'Unknown') as category,
        COUNT(DISTINCT oi.order_id) as orders,
        ROUND(SUM(oi.price), 2) as revenue,
        ROUND(AVG(oi.price), 2) as avg_price
    FROM order_items oi
    LEFT JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN categories ct ON p.product_category_name = ct.product_category_name
    GROUP BY category
    ORDER BY revenue DESC
    LIMIT 10
""", conn)
print(q3.to_string(index=False))

# ── Q4: Review Score vs Delivery Time ─────────────────
print("\n📊 Q4 — Review Score vs Delivery Days:")
q4 = pd.read_sql_query("""
    SELECT 
        r.review_score,
        COUNT(*) as order_count,
        ROUND(AVG(JULIANDAY(o.order_delivered_customer_date) - 
              JULIANDAY(o.order_purchase_timestamp)), 1) as avg_delivery_days,
        ROUND(AVG(oi.price), 2) as avg_order_value
    FROM reviews r
    JOIN orders o ON r.order_id = o.order_id
    JOIN order_items oi ON r.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    GROUP BY r.review_score
    ORDER BY r.review_score DESC
""", conn)
print(q4.to_string(index=False))

# ── Q5: Payment Method Analysis ───────────────────────
print("\n📊 Q5 — Payment Methods:")
q5 = pd.read_sql_query("""
    SELECT 
        payment_type,
        COUNT(DISTINCT order_id) as orders,
        ROUND(SUM(payment_value), 2) as total_value,
        ROUND(AVG(payment_value), 2) as avg_value,
        ROUND(COUNT(DISTINCT order_id) * 100.0 / 
              (SELECT COUNT(DISTINCT order_id) FROM payments), 2) as pct
    FROM payments
    GROUP BY payment_type
    ORDER BY orders DESC
""", conn)
print(q5.to_string(index=False))

# ── Q6: Monthly Order Trend ────────────────────────────
print("\n📊 Q6 — Monthly Order Trend:")
q6 = pd.read_sql_query("""
    SELECT 
        SUBSTR(order_purchase_timestamp, 1, 7) as month,
        COUNT(*) as orders,
        ROUND(COUNT(*) * 1.0 / 
              LAG(COUNT(*)) OVER (ORDER BY SUBSTR(order_purchase_timestamp,1,7)) * 100 - 100
              , 1) as mom_growth_pct
    FROM orders
    GROUP BY month
    ORDER BY month
""", conn)
print(q6.tail(12).to_string(index=False))

# ── Q7: Late Delivery Impact on Reviews ───────────────
print("\n📊 Q7 — Late Delivery Impact on Review Scores:")
q7 = pd.read_sql_query("""
    SELECT
        CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
             THEN 'Late' ELSE 'On Time'
        END as delivery_status,
        COUNT(*) as orders,
        ROUND(AVG(r.review_score), 2) as avg_review_score,
        ROUND(AVG(JULIANDAY(o.order_delivered_customer_date) - 
              JULIANDAY(o.order_purchase_timestamp)), 1) as avg_days
    FROM orders o
    JOIN reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    GROUP BY delivery_status
""", conn)
print(q7.to_string(index=False))

# ── Q8: Customer Repeat Purchase ──────────────────────
print("\n📊 Q8 — Customer Repeat Purchase Rate:")
q8 = pd.read_sql_query("""
    SELECT
        CASE WHEN order_count = 1 THEN 'One-time'
             WHEN order_count = 2 THEN 'Two orders'
             ELSE 'Three or more'
        END as customer_type,
        COUNT(*) as customers,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as pct
    FROM (
        SELECT customer_unique_id, COUNT(*) as order_count
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY customer_unique_id
    )
    GROUP BY customer_type
    ORDER BY customers DESC
""", conn)
print(q8.to_string(index=False))

conn.close()
print("\n✅ All 8 queries complete")