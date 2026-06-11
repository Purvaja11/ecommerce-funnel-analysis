import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# ── Setup ──────────────────────────────────────────────
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
conn = sqlite3.connect(os.path.join(base_dir, 'data', 'olist.db'))
os.makedirs(os.path.join(base_dir, 'charts'), exist_ok=True)
charts_dir = os.path.join(base_dir, 'charts')

TEAL = '#00D4B4'
BLUE = '#4A9EFF'
RED  = '#FF6B6B'
DARK = '#1A2535'
GRAY = '#8899AA'

# ══════════════════════════════════════════════════════
# CHART 1 — Order Status Funnel
# ══════════════════════════════════════════════════════
df1 = pd.read_sql_query("""
    SELECT order_status, COUNT(*) as count
    FROM orders
    GROUP BY order_status
    ORDER BY count DESC
""", conn)

fig1 = go.Figure(go.Funnel(
    y=df1['order_status'],
    x=df1['count'],
    textinfo='value+percent initial',
    marker=dict(color=[TEAL, BLUE, RED, RED, GRAY, GRAY, GRAY, GRAY]),
    connector=dict(line=dict(color=DARK, width=2))
))
fig1.update_layout(
    title=dict(
        text='<b>E-Commerce Order Status Funnel</b><br>'
             '<sup>97% of orders delivered — cancellations and unavailability are minimal</sup>',
        font=dict(size=16)
    ),
    plot_bgcolor='white', paper_bgcolor='white', height=450
)
fig1.write_image(os.path.join(charts_dir, 'chart1_order_funnel.png'), scale=2)
fig1.show()
print("✅ Chart 1 saved")

# ══════════════════════════════════════════════════════
# CHART 2 — Delivery Days vs Review Score
# ══════════════════════════════════════════════════════
df2 = pd.read_sql_query("""
    SELECT 
        r.review_score,
        COUNT(*) as order_count,
        ROUND(AVG(JULIANDAY(o.order_delivered_customer_date) - 
              JULIANDAY(o.order_purchase_timestamp)), 1) as avg_delivery_days
    FROM reviews r
    JOIN orders o ON r.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    GROUP BY r.review_score
    ORDER BY r.review_score
""", conn)

fig2 = make_subplots(specs=[[{"secondary_y": True}]])
bar_colors = [RED, RED, GRAY, BLUE, TEAL]
fig2.add_trace(go.Bar(
    x=df2['review_score'], y=df2['order_count'],
    name='Order Count', marker_color=bar_colors,
    text=df2['order_count'], textposition='outside'
), secondary_y=False)
fig2.add_trace(go.Scatter(
    x=df2['review_score'], y=df2['avg_delivery_days'],
    name='Avg Delivery Days', mode='lines+markers',
    marker=dict(size=12, color='#F18F01'),
    line=dict(width=3, color='#F18F01')
), secondary_y=True)
fig2.update_layout(
    title=dict(
        text='<b>Review Score vs Delivery Days</b><br>'
             '<sup>1-star orders take 19.6 days avg — 5-star orders take 10.7 days</sup>',
        font=dict(size=16)
    ),
    plot_bgcolor='white', paper_bgcolor='white', height=420,
    xaxis=dict(title='Review Score', gridcolor='#f0f0f0'),
    legend=dict(orientation='h', y=1.1)
)
fig2.update_yaxes(title_text='Order Count', gridcolor='#f0f0f0',
                  secondary_y=False)
fig2.update_yaxes(title_text='Avg Delivery Days', secondary_y=True)
fig2.write_image(os.path.join(charts_dir, 'chart2_review_delivery.png'), scale=2)
fig2.show()
print("✅ Chart 2 saved")

# ══════════════════════════════════════════════════════
# CHART 3 — Top 10 Categories by Revenue
# ══════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════
# CHART 3 — Top 10 Categories by Revenue
# ══════════════════════════════════════════════════════
df3 = pd.read_sql_query("""
    SELECT 
        COALESCE(ct.product_category_name_english, 
                 p.product_category_name, 'Unknown') as category,
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

fig3 = go.Figure()

fig3.add_trace(go.Bar(
    y=df3['category'], x=df3['revenue'],
    name='Revenue', orientation='h',
    marker_color=TEAL,
    text=['${:,.0f}'.format(v) for v in df3['revenue']],
    textposition='outside'
))

fig3.add_trace(go.Scatter(
    y=df3['category'], x=df3['avg_price'],
    name='Avg Price ($)',
    mode='markers',
    marker=dict(size=14, color='#F18F01', symbol='diamond'),
    xaxis='x2'
))

fig3.update_layout(
    title=dict(
        text='<b>Top 10 Categories by Revenue</b><br><sup>Health and Beauty leads with $1.26M — Watches have highest avg price at $201</sup>',
        font=dict(size=16)
    ),
    xaxis=dict(
        title='Total Revenue ($)',
        tickformat='$,.0f',
        gridcolor='#f0f0f0',
        side='bottom'
    ),
    xaxis2=dict(
        title='Avg Price ($)',
        tickformat='$,.0f',
        overlaying='x',
        side='top',
        showgrid=False
    ),
    plot_bgcolor='white', paper_bgcolor='white',
    height=480, margin=dict(l=180, r=80, t=100),
    legend=dict(orientation='h', y=1.15)
)

fig3.write_image(os.path.join(charts_dir, 'chart3_category_revenue.png'), scale=2)
fig3.show()
print("✅ Chart 3 saved")

# ══════════════════════════════════════════════════════
# CHART 4 — Late Delivery Impact
# ══════════════════════════════════════════════════════
df4 = pd.read_sql_query("""
    SELECT
        CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
             THEN 'Late Delivery' ELSE 'On-Time Delivery'
        END as delivery_status,
        COUNT(*) as orders,
        ROUND(AVG(r.review_score), 2) as avg_review,
        ROUND(AVG(JULIANDAY(o.order_delivered_customer_date) - 
              JULIANDAY(o.order_purchase_timestamp)), 1) as avg_days
    FROM orders o
    JOIN reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    GROUP BY delivery_status
""", conn)

fig4 = make_subplots(rows=1, cols=2,
    subplot_titles=('Avg Review Score', 'Avg Delivery Days'))
colors = [RED, TEAL]
fig4.add_trace(go.Bar(
    x=df4['delivery_status'], y=df4['avg_review'],
    marker_color=colors, showlegend=False,
    text=[f"{v:.2f} ⭐" for v in df4['avg_review']],
    textposition='outside'
), row=1, col=1)
fig4.add_trace(go.Bar(
    x=df4['delivery_status'], y=df4['avg_days'],
    marker_color=colors, showlegend=False,
    text=[f"{v:.1f} days" for v in df4['avg_days']],
    textposition='outside'
), row=1, col=2)
fig4.update_layout(
    title=dict(
        text='<b>Late Delivery Impact on Customer Satisfaction</b><br>'
             '<sup>Late orders score 2.57 stars vs 4.29 for on-time — 40% lower satisfaction</sup>',
        font=dict(size=16)
    ),
    plot_bgcolor='white', paper_bgcolor='white', height=420
)
fig4.update_yaxes(gridcolor='#f0f0f0')
fig4.write_image(os.path.join(charts_dir, 'chart4_late_delivery_impact.png'), scale=2)
fig4.show()
print("✅ Chart 4 saved")

# ══════════════════════════════════════════════════════
# CHART 5 — Payment Methods
# ══════════════════════════════════════════════════════
df5 = pd.read_sql_query("""
    SELECT payment_type,
           COUNT(DISTINCT order_id) as orders,
           ROUND(AVG(payment_value), 2) as avg_value
    FROM payments
    WHERE payment_type != 'not_defined'
    GROUP BY payment_type
    ORDER BY orders DESC
""", conn)

fig5 = make_subplots(rows=1, cols=2,
    subplot_titles=('Orders by Payment Method',
                    'Avg Order Value by Method'),
    specs=[[{"type": "pie"}, {"type": "bar"}]])
fig5.add_trace(go.Pie(
    labels=df5['payment_type'],
    values=df5['orders'],
    hole=0.45,
    marker=dict(colors=[TEAL, BLUE, '#F18F01', RED])
), row=1, col=1)
fig5.add_trace(go.Bar(
    x=df5['payment_type'], y=df5['avg_value'],
    marker_color=[TEAL, BLUE, '#F18F01', RED],
    text=['${:.0f}'.format(v) for v in df5['avg_value']],
    textposition='outside', showlegend=False
), row=1, col=2)
fig5.update_layout(
    title=dict(
        text='<b>Payment Method Analysis</b><br>'
             '<sup>Credit card dominates at 76.9% — boleto still strong at 19.9%</sup>',
        font=dict(size=16)
    ),
    plot_bgcolor='white', paper_bgcolor='white', height=420
)
fig5.write_image(os.path.join(charts_dir, 'chart5_payment_methods.png'), scale=2)
fig5.show()
print("✅ Chart 5 saved")

# ══════════════════════════════════════════════════════
# CHART 6 — Monthly Order Trend + Customer Retention
# ══════════════════════════════════════════════════════
df6 = pd.read_sql_query("""
    SELECT 
        SUBSTR(order_purchase_timestamp, 1, 7) as month,
        COUNT(*) as orders
    FROM orders
    WHERE SUBSTR(order_purchase_timestamp, 1, 7) BETWEEN '2017-01' AND '2018-08'
    GROUP BY month
    ORDER BY month
""", conn)

df7 = pd.read_sql_query("""
    SELECT
        CASE WHEN order_count = 1 THEN 'One-time (96.9%)'
             WHEN order_count = 2 THEN 'Two orders (2.9%)'
             ELSE 'Three+ (0.3%)'
        END as customer_type,
        COUNT(*) as customers
    FROM (
        SELECT customer_unique_id, COUNT(*) as order_count
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY customer_unique_id
    )
    GROUP BY customer_type
    ORDER BY customers DESC
""", conn)

fig6 = make_subplots(
    rows=1, cols=2,
    specs=[[{"type": "scatter"}, {"type": "pie"}]]
)

fig6.add_trace(go.Scatter(
    x=df6['month'], y=df6['orders'],
    mode='lines+markers',
    line=dict(color=TEAL, width=3),
    marker=dict(size=8, color=TEAL),
    fill='tozeroy', fillcolor='rgba(0,212,180,0.1)',
    showlegend=False
), row=1, col=1)

fig6.add_trace(go.Pie(
    labels=df7['customer_type'],
    values=df7['customers'],
    hole=0.45,
    marker=dict(colors=[RED, BLUE, TEAL])
), row=1, col=2)

fig6.update_layout(
    title=dict(
        text='<b>Growth Trend & Customer Retention</b><br>'
             '<sup>96.9% customers never return — retention is the #1 business problem</sup>',
        font=dict(size=16)
    ),
    plot_bgcolor='white', paper_bgcolor='white',
    height=450,
    margin=dict(t=100)
)
fig6.update_xaxes(tickangle=45, gridcolor='#f0f0f0', row=1, col=1)
fig6.update_yaxes(gridcolor='#f0f0f0', row=1, col=1)

fig6.write_image(os.path.join(charts_dir, 'chart6_growth_retention.png'), scale=2)
fig6.show()
print("✅ Chart 6 saved")

conn.close()
print("\n✅ All 6 charts saved to /charts folder")