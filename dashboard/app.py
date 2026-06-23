import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# ── Page config ────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Funnel Analysis",
    page_icon="🛍️",
    layout="wide"
)

# ── Load data ──────────────────────────────────────────
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')

    orders = pd.read_csv(os.path.join(data_dir, 'orders_clean.csv'))
    items = pd.read_csv(os.path.join(data_dir, 'items_clean.csv'))
    reviews = pd.read_csv(os.path.join(data_dir, 'reviews_clean.csv'))
    customers = pd.read_csv(os.path.join(data_dir, 'customers_clean.csv'))
    products = pd.read_csv(os.path.join(data_dir, 'products_clean.csv'))
    payments = pd.read_csv(os.path.join(data_dir, 'payments_clean.csv'))

    return orders, items, reviews, customers, products, payments

orders, items, reviews, customers, products, payments = load_data()

TEAL = '#E94560'
BLUE = '#F5A623'
GOLD = '#A855F7'
GREEN = '#10B981'

# ── Sidebar filters ────────────────────────────────────
st.sidebar.title("🔍 Filters")
status_options = orders['order_status'].unique().tolist()
selected_status = st.sidebar.multiselect(
    "Order Status", options=status_options, default=status_options
)

filtered_orders = orders[orders['order_status'].isin(selected_status)]

# ── Title ──────────────────────────────────────────────
st.title("🛍️ E-Commerce Funnel Analysis")
st.caption("Olist Brazilian E-Commerce Dataset | 99,441 orders | 2016–2018")
st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "🚚 Delivery & Satisfaction",
    "💰 Revenue & Category",
    "👥 Customer & Retention"
])

# ══════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    total_orders = len(filtered_orders)
    delivered = len(filtered_orders[filtered_orders['order_status']=='delivered'])
    delivery_rate = delivered/total_orders*100 if total_orders > 0 else 0
    avg_review = reviews['review_score'].mean()

    col1.metric("Total Orders", f"{total_orders:,}")
    col2.metric("Delivered Orders", f"{delivered:,}")
    col3.metric("Delivery Rate", f"{delivery_rate:.2f}%")
    col4.metric("Avg Review Score", f"{avg_review:.2f} ⭐")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        status_counts = orders['order_status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']
        fig1 = go.Figure(go.Funnel(
            y=status_counts['status'],
            x=status_counts['count'],
            textinfo='value+percent initial',
            marker=dict(color=TEAL)
        ))
        fig1.update_layout(title='Order Status Funnel',
                           plot_bgcolor='white', height=400)
        st.plotly_chart(fig1, use_container_width=True)

    with col_r:
        orders['year_month'] = pd.to_datetime(
            orders['order_purchase_timestamp']
        ).dt.to_period('M').astype(str)
        monthly = orders[
            (orders['year_month'] >= '2017-01') & 
            (orders['year_month'] <= '2018-08')
        ].groupby('year_month').size().reset_index(name='orders')
        fig2 = px.area(monthly, x='year_month', y='orders',
                       title='Monthly Order Volume',
                       color_discrete_sequence=[TEAL])
        fig2.update_layout(plot_bgcolor='white', height=400,
                           xaxis=dict(tickangle=45))
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("💡 Key Business Insights")
    i1, i2, i3 = st.columns(3)
    i1.success("**Healthy Funnel**\n97% of orders get delivered — cancellations are minimal")
    i2.warning("**Delivery is the Risk**\nLate orders score 2.57⭐ vs 4.29⭐ on-time")
    i3.error("**Retention Crisis**\n96.9% of customers never order again")

# ══════════════════════════════════════════════════════
# TAB 2 — DELIVERY & SATISFACTION
# ══════════════════════════════════════════════════════
with tab2:
    delivered_orders = orders[
        (orders['order_status']=='delivered') &
        (orders['order_delivered_customer_date'].notna())
    ].copy()

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Delivery Days", f"{delivered_orders['delivery_days'].mean():.1f}")
    col2.metric("Late Deliveries", f"{delivered_orders['is_late'].sum():,.0f}")
    col3.metric("Late Rate", f"{delivered_orders['is_late'].mean()*100:.2f}%")

    col_l, col_r = st.columns(2)

    with col_l:
        merged = delivered_orders.merge(reviews[['order_id','review_score']], on='order_id')
        review_delivery = merged.groupby('review_score').agg(
            count=('order_id','count'),
            avg_days=('delivery_days','mean')
        ).reset_index()

        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(go.Bar(
            x=review_delivery['review_score'], y=review_delivery['count'],
            name='Order Count', marker_color=TEAL
        ), secondary_y=False)
        fig3.add_trace(go.Scatter(
            x=review_delivery['review_score'], y=review_delivery['avg_days'],
            name='Avg Delivery Days', mode='lines+markers',
            marker=dict(size=10, color=BLUE), line=dict(width=3, color=BLUE)
        ), secondary_y=True)
        fig3.update_layout(title='Review Score vs Delivery Days',
                           plot_bgcolor='white', height=400)
        st.plotly_chart(fig3, use_container_width=True)

    with col_r:
        late_compare = merged.copy()
        late_compare['status'] = late_compare['is_late'].map({1:'Late',0:'On-Time'})
        comp = late_compare.groupby('status').agg(
            avg_review=('review_score','mean'),
            avg_days=('delivery_days','mean')
        ).reset_index()

        fig4 = px.bar(comp, x='status', y='avg_review',
                      color='status',
                      color_discrete_map={'Late':TEAL,'On-Time':GREEN},
                      title='Avg Review Score: Late vs On-Time',
                      text=[f"{v:.2f}⭐" for v in comp['avg_review']])
        fig4.update_traces(textposition='outside')
        fig4.update_layout(plot_bgcolor='white', height=400, showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

    st.error("**Critical Finding:** Late orders average 31.4 days delivery vs 10.9 for on-time — and score 40% lower in customer satisfaction.")

# ══════════════════════════════════════════════════════
# TAB 3 — REVENUE & CATEGORY
# ══════════════════════════════════════════════════════
with tab3:
    total_revenue = items['price'].sum()
    col1, col2 = st.columns(2)
    col1.metric("Total Revenue", f"${total_revenue:,.0f}")
    col2.metric("Total Items Sold", f"{len(items):,}")

    cat_revenue = items.merge(products[['product_id','category_english']], on='product_id')
    cat_summary = cat_revenue.groupby('category_english').agg(
        revenue=('price','sum'),
        orders=('order_id','nunique')
    ).reset_index().nlargest(10, 'revenue')

    fig5 = px.bar(cat_summary, y='category_english', x='revenue',
                  orientation='h', color_discrete_sequence=[TEAL],
                  title='Top 10 Categories by Revenue',
                  text=[f"${v:,.0f}" for v in cat_summary['revenue']])
    fig5.update_traces(textposition='outside')
    fig5.update_layout(plot_bgcolor='white', height=450,
                       yaxis=dict(categoryorder='total ascending'))
    st.plotly_chart(fig5, use_container_width=True)

    col_l, col_r = st.columns(2)
    with col_l:
        pay_summary = payments[payments['payment_type']!='not_defined'].groupby(
            'payment_type'
        ).size().reset_index(name='count')
        fig6 = px.pie(pay_summary, values='count', names='payment_type',
                      hole=0.45, title='Payment Method Distribution',
                      color_discrete_sequence=[TEAL,BLUE,GOLD,GREEN])
        fig6.update_layout(height=400)
        st.plotly_chart(fig6, use_container_width=True)

    with col_r:
        state_rev = items.merge(
            orders[['order_id','customer_id']], on='order_id'
        ).merge(
            customers[['customer_id','customer_state']], on='customer_id'
        ).groupby('customer_state')['price'].sum().reset_index().nlargest(10,'price')
        fig7 = px.bar(state_rev, x='customer_state', y='price',
                      color_discrete_sequence=[TEAL],
                      title='Top 10 States by Revenue')
        fig7.update_layout(plot_bgcolor='white', height=400)
        st.plotly_chart(fig7, use_container_width=True)

# ══════════════════════════════════════════════════════
# TAB 4 — CUSTOMER & RETENTION
# ══════════════════════════════════════════════════════
with tab4:
    cust_orders = customers.merge(orders[['order_id','customer_id']], on='customer_id')
    cust_counts = cust_orders.groupby('customer_unique_id').size().reset_index(name='order_count')
    cust_counts['type'] = cust_counts['order_count'].apply(
        lambda x: 'One-time' if x==1 else ('Two orders' if x==2 else 'Three+')
    )
    retention = cust_counts['type'].value_counts().reset_index()
    retention.columns = ['type','customers']

    col1, col2 = st.columns(2)

    with col1:
        fig8 = px.pie(retention, values='customers', names='type',
                      hole=0.45, title='Customer Retention Rate',
                      color_discrete_sequence=[TEAL,BLUE,GREEN])
        fig8.update_layout(height=400)
        st.plotly_chart(fig8, use_container_width=True)

    with col2:
        state_orders = customers['customer_state'].value_counts().reset_index().head(10)
        state_orders.columns = ['state','customers']
        fig9 = px.bar(state_orders, x='state', y='customers',
                      color_discrete_sequence=[TEAL],
                      title='Top 10 States by Customer Count')
        fig9.update_layout(plot_bgcolor='white', height=400)
        st.plotly_chart(fig9, use_container_width=True)

    st.error("**Retention Crisis:** 96.9% of customers never place a second order. Only 0.3% become repeat (3+) customers — indicating minimal post-purchase engagement.")

    st.divider()
    st.subheader("🔎 Raw Data Explorer")
    st.dataframe(
        orders[['order_id','order_status','delivery_days','is_late']].head(100),
        use_container_width=True, height=300
    )