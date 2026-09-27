"""
Olist E-commerce Analytics: interactive dashboard (Streamlit)

Run locally (from the project folder, .venv active):
    streamlit run dashboard/app.py

How Streamlit works: this script runs top to bottom every time the user changes
a filter. st.* functions draw things on the page. @st.cache_data remembers the
result of slow functions (like loading data) so they only run once.
"""
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"

# Colour-blind-safe palette (same as the notebook charts)
BLUE, ORANGE, AQUA, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#898781"

st.set_page_config(page_title="Olist E-commerce Analytics", page_icon="📦", layout="wide")


# ---------------------------------------------------------------- data loading
@st.cache_data
def load(name: str) -> pd.DataFrame:
    """Read one Parquet file (exported by src/export_dashboard_data.py) with DuckDB."""
    return duckdb.sql(f"SELECT * FROM '{(DATA_DIR / f'{name}.parquet').as_posix()}'").df()


orders = load("orders")
items = load("items")
rfm = load("rfm")
sellers = load("sellers")

orders["month"] = pd.to_datetime(orders["order_date"]).dt.strftime("%Y-%m")
items["month"] = pd.to_datetime(items["order_date"]).dt.strftime("%Y-%m")


def style(fig, height=380):
    """Consistent, clean look for every Plotly chart."""
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13), title_font=dict(size=16), hoverlabel=dict(font_size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1, title=None),
    )
    fig.update_xaxes(showgrid=False, title=None)
    fig.update_yaxes(gridcolor="rgba(137,135,129,0.25)", title=None, zeroline=False)
    return fig


# ---------------------------------------------------------------- sidebar filters
st.sidebar.title("Filters")
months = sorted(orders["month"].unique())
start, end = st.sidebar.select_slider("Order month", options=months, value=(months[0], months[-1]))
all_states = sorted(orders["customer_state"].dropna().unique())
states = st.sidebar.multiselect("Customer state", all_states, placeholder="All states")
st.sidebar.caption("Filters apply to orders, revenue, customers and delivery. "
                   "RFM segments use the state filter only; the seller scorecard covers all data.")
st.sidebar.markdown("---")
st.sidebar.markdown("**Data:** [Olist public dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) · "
                    "Jan 2017 – Aug 2018 · canceled/unavailable orders excluded")


def apply_filters(df):
    out = df[(df["month"] >= start) & (df["month"] <= end)]
    if states:
        out = out[out["customer_state"].isin(states)]
    return out


o = apply_filters(orders)
i = apply_filters(items)
r = rfm[rfm["customer_state"].isin(states)] if states else rfm

# ---------------------------------------------------------------- header & KPIs
st.title("📦 Olist E-commerce Analytics")
st.caption("End-to-end analysis of ~100k orders from a Brazilian marketplace · "
           "Built with SQL (DuckDB), Python and Streamlit")

if o.empty:
    st.warning("No orders match these filters. Widen the date range or clear the state filter.")
    st.stop()

delivered = o[o["is_late"].notna()]
customers = o["customer_key"].nunique()
repeaters = (o.groupby("customer_key").size() > 1).sum()

k = st.columns(6)
k[0].metric("Revenue", f"R$ {o['order_revenue'].sum() / 1e6:,.1f}M")
k[1].metric("Orders", f"{len(o):,}")
k[2].metric("Customers", f"{customers:,}")
k[3].metric("Avg order value", f"R$ {o['order_revenue'].mean():,.0f}")
k[4].metric("Late deliveries", f"{100 * delivered['is_late'].mean():.1f}%")
k[5].metric("Avg review", f"{o['review_score'].mean():.2f} ★")

tab_overview, tab_customers, tab_delivery, tab_sellers, tab_insights = st.tabs(
    ["📈 Revenue", "👥 Customers", "🚚 Delivery", "🏪 Sellers", "💡 Key insights"]
)

# ---------------------------------------------------------------- tab: revenue
with tab_overview:
    monthly = o.groupby("month").agg(revenue=("order_revenue", "sum"), orders=("order_revenue", "size")).reset_index()
    monthly["aov"] = monthly["revenue"] / monthly["orders"]
    fig = px.bar(monthly, x="month", y="revenue", title="Monthly revenue",
                 color_discrete_sequence=[BLUE], custom_data=["orders", "aov"])
    fig.update_traces(hovertemplate="<b>%{x}</b><br>Revenue: R$ %{y:,.0f}<br>"
                                    "Orders: %{customdata[0]:,}<br>AOV: R$ %{customdata[1]:,.0f}<extra></extra>")
    fig.update_yaxes(tickprefix="R$ ", tickformat="~s")
    st.plotly_chart(style(fig), width="stretch")

    c1, c2 = st.columns(2)
    cats = (i.groupby("category")["item_revenue"].sum().sort_values(ascending=False).head(10)
             .reset_index().sort_values("item_revenue"))
    fig = px.bar(cats, x="item_revenue", y="category", orientation="h", title="Top 10 categories by revenue",
                 color_discrete_sequence=[BLUE])
    fig.update_traces(hovertemplate="<b>%{y}</b><br>R$ %{x:,.0f}<extra></extra>")
    fig.update_xaxes(tickprefix="R$ ", tickformat="~s", showgrid=True, gridcolor="rgba(137,135,129,0.25)")
    fig.update_yaxes(showgrid=False)
    c1.plotly_chart(style(fig, 420), width="stretch")

    pay = (o.dropna(subset=["main_payment_type"]).groupby("main_payment_type")
             .agg(orders=("order_revenue", "size"), aov=("order_revenue", "mean")).reset_index()
             .sort_values("orders", ascending=False))
    pay["share"] = 100 * pay["orders"] / pay["orders"].sum()
    fig = px.bar(pay, x="main_payment_type", y="share", title="Payment method (% of orders)",
                 color_discrete_sequence=[AQUA], custom_data=["orders", "aov"], text=pay["share"].round(1).astype(str) + "%")
    fig.update_traces(textposition="outside", cliponaxis=False,
                      hovertemplate="<b>%{x}</b><br>%{y:.1f}% of orders (%{customdata[0]:,})<br>"
                                    "AOV: R$ %{customdata[1]:,.0f}<extra></extra>")
    fig.update_yaxes(ticksuffix="%")
    c2.plotly_chart(style(fig, 420), width="stretch")

# ---------------------------------------------------------------- tab: customers
with tab_customers:
    c1, c2, c3 = st.columns(3)
    c1.metric("Customers who ordered 2+ times", f"{100 * repeaters / customers:.1f}%")
    c2.metric("Revenue per customer", f"R$ {o['order_revenue'].sum() / customers:,.0f}")
    c3.metric("Customers in RFM view", f"{len(r):,}")

    seg = (r.groupby("segment").agg(customers=("monetary", "size"), revenue=("monetary", "sum"),
                                    avg_spend=("monetary", "mean"), avg_recency=("recency_days", "mean"))
             .reset_index())
    seg["% of customers"] = 100 * seg["customers"] / seg["customers"].sum()
    seg["% of revenue"] = 100 * seg["revenue"] / seg["revenue"].sum()
    seg = seg.sort_values("revenue")
    fig = go.Figure()
    fig.add_bar(y=seg["segment"], x=seg["% of customers"], orientation="h", name="% of customers", marker_color=GREY,
                hovertemplate="%{y}: %{x:.1f}% of customers<extra></extra>")
    fig.add_bar(y=seg["segment"], x=seg["% of revenue"], orientation="h", name="% of revenue", marker_color=BLUE,
                hovertemplate="%{y}: %{x:.1f}% of revenue<extra></extra>")
    fig.update_layout(barmode="group", title="RFM segments: share of customers vs share of revenue")
    fig.update_xaxes(ticksuffix="%", showgrid=True, gridcolor="rgba(137,135,129,0.25)")
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(style(fig, 440), width="stretch")

    actions = {
        "Champions": "Reward & referral program",
        "Loyal (lapsing)": "Personalised win-back",
        "New big spenders": "Nurture toward a 2nd purchase",
        "New customers": "Welcome series",
        "Needs attention": "Reminder offers",
        "At risk: big spenders": "High-value win-back campaign",
        "Lost / one-off": "Low-cost or no spend",
    }
    table = seg.sort_values("revenue", ascending=False).assign(action=lambda d: d["segment"].map(actions))
    st.dataframe(
        table[["segment", "customers", "% of customers", "% of revenue", "avg_spend", "avg_recency", "action"]],
        hide_index=True, width="stretch",
        column_config={
            "% of customers": st.column_config.NumberColumn(format="%.1f%%"),
            "% of revenue": st.column_config.NumberColumn(format="%.1f%%"),
            "avg_spend": st.column_config.NumberColumn("avg spend", format="R$ %.0f"),
            "avg_recency": st.column_config.NumberColumn("avg days since order", format="%.0f"),
        },
    )

    by_state = (o.groupby("customer_state").agg(revenue=("order_revenue", "sum"), customers=("customer_key", "nunique"))
                  .reset_index().sort_values("revenue", ascending=False).head(10).sort_values("revenue"))
    fig = px.bar(by_state, x="revenue", y="customer_state", orientation="h", title="Revenue by customer state (top 10)",
                 color_discrete_sequence=[BLUE], custom_data=["customers"])
    fig.update_traces(hovertemplate="<b>%{y}</b><br>R$ %{x:,.0f}<br>%{customdata[0]:,} customers<extra></extra>")
    fig.update_xaxes(tickprefix="R$ ", tickformat="~s", showgrid=True, gridcolor="rgba(137,135,129,0.25)")
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(style(fig, 400), width="stretch")

# ---------------------------------------------------------------- tab: delivery
with tab_delivery:
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg delivery time", f"{delivered['delivery_days'].mean():.1f} days")
    c2.metric("Avg days vs estimate", f"{delivered['days_vs_estimate'].mean():+.1f} days",
              help="Negative = arrived before the estimated date")
    c3.metric("Review: late vs on time",
              f"{delivered.loc[delivered.is_late == True, 'review_score'].mean():.2f}★ vs "
              f"{delivered.loc[delivered.is_late == False, 'review_score'].mean():.2f}★")

    lm = delivered.groupby("month")["is_late"].mean().mul(100).reset_index(name="late_pct")
    fig = px.bar(lm, x="month", y="late_pct", title="Late delivery rate by month", color_discrete_sequence=[BLUE])
    fig.update_traces(marker_color=[ORANGE if v > 10 else BLUE for v in lm["late_pct"]],
                      hovertemplate="<b>%{x}</b><br>%{y:.1f}% late<extra></extra>")
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(style(fig), width="stretch")

    c1, c2 = st.columns(2)
    bins = [-1000, -10, -1, 0, 3, 7, 1000]
    labels = ["10+ days early", "1-9 days early", "on the day", "1-3 days late", "4-7 days late", "8+ days late"]
    d = delivered.dropna(subset=["review_score"]).copy()
    d["arrival"] = pd.cut(d["days_vs_estimate"], bins=bins, labels=labels)
    rb = d.groupby("arrival", observed=True)["review_score"].agg(["mean", "size"]).reset_index()
    fig = px.bar(rb, x="arrival", y="mean", title="Average review by arrival vs estimate",
                 custom_data=["size"], text=rb["mean"].round(2).astype(str) + "★")
    fig.update_traces(marker_color=[BLUE] * 3 + [ORANGE] * 3, textposition="outside", cliponaxis=False,
                      hovertemplate="<b>%{x}</b><br>%{y:.2f}★ (%{customdata[0]:,} orders)<extra></extra>")
    fig.update_yaxes(range=[0, 5.2])
    c1.plotly_chart(style(fig, 420), width="stretch")

    ls = (delivered.groupby("customer_state").agg(late_pct=("is_late", "mean"), orders=("is_late", "size"),
                                                  days=("delivery_days", "mean")).reset_index())
    ls = ls[ls["orders"] >= 100]
    ls["late_pct"] *= 100
    ls = ls.sort_values("late_pct", ascending=False).head(10).sort_values("late_pct")
    fig = px.bar(ls, x="late_pct", y="customer_state", orientation="h",
                 title="States with the highest late rate (100+ orders)", color_discrete_sequence=[ORANGE],
                 custom_data=["orders", "days"])
    fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x:.1f}% late<br>%{customdata[0]:,} orders · "
                                    "avg %{customdata[1]:.1f} days<extra></extra>")
    fig.update_xaxes(ticksuffix="%", showgrid=True, gridcolor="rgba(137,135,129,0.25)")
    fig.update_yaxes(showgrid=False)
    c2.plotly_chart(style(fig, 420), width="stretch")

# ---------------------------------------------------------------- tab: sellers
with tab_sellers:
    st.caption("Seller scorecard across the full period. Underperforming = 30+ orders and "
               "(late rate > 15% or average review < 3.5).")
    counts = sellers["performance_flag"].value_counts()
    top10_share = sellers.nlargest(int(len(sellers) * 0.1), "revenue")["revenue"].sum() / sellers["revenue"].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Sellers", f"{len(sellers):,}")
    c2.metric("Underperforming sellers (30+ orders)", f"{counts.get('Underperforming', 0)}")
    c3.metric("Revenue from top 10% of sellers", f"{100 * top10_share:.0f}%")

    established = sellers[sellers["performance_flag"] != "Low volume"].copy()
    established["late %"] = established["late_rate"] * 100
    fig = px.scatter(established, x="late %", y="avg_review", size="revenue", color="performance_flag",
                     color_discrete_map={"Good": BLUE, "Underperforming": ORANGE}, size_max=40, opacity=0.65,
                     hover_name="seller", hover_data={"revenue": ":,.0f", "orders": True, "seller_state": True,
                                                      "late %": ":.1f", "avg_review": ":.2f", "performance_flag": False},
                     title="Seller scorecard (30+ orders) · bubble size = revenue")
    fig.add_vline(x=15, line_dash="dash", line_color=GREY)
    fig.add_hline(y=3.5, line_dash="dash", line_color=GREY)
    style(fig, 480)
    fig.update_xaxes(ticksuffix="%", title="late delivery rate")
    fig.update_yaxes(title="average review")
    st.plotly_chart(fig, width="stretch")

    flag = st.radio("Show", ["Underperforming", "Good", "Low volume", "All"], horizontal=True)
    view = sellers if flag == "All" else sellers[sellers["performance_flag"] == flag]
    st.dataframe(
        view.sort_values("revenue", ascending=False)
            [["revenue_rank", "seller", "seller_state", "orders", "revenue", "avg_review", "late_rate", "avg_handling_days", "performance_flag"]],
        hide_index=True, width="stretch",
        column_config={
            "revenue": st.column_config.NumberColumn(format="R$ %.0f"),
            "late_rate": st.column_config.NumberColumn("late rate", format="%.3f"),
            "avg_handling_days": st.column_config.NumberColumn("handling days", format="%.1f"),
        },
    )

# ---------------------------------------------------------------- tab: insights
with tab_insights:
    st.subheader("Key findings")
    st.markdown("""
1. **Growth has stalled.** Jan–Aug revenue grew **+140% YoY**, but monthly revenue has been flat at ~R$ 1.0–1.15M all of 2018.
2. **Growth came from volume, not basket size.** Orders grew ~8× while average order value stayed at ~R$ 160.
3. **Almost nobody comes back.** ~97% of customers order once; ~30% of "repeat" orders are same-day split baskets, so the **true repeat rate is ≈ 2%**.
4. **Two RFM segments drive the business:** new and at-risk big spenders are ~30% of customers but **~56% of revenue**.
5. **Lateness destroys satisfaction.** Late orders average **2.3★ vs 4.3★** (t-test p≈0, Cohen's d = 1.47), and a late *first* delivery cuts repeat purchases by **~19%** (chi-square p≈0.01).
6. **The carrier leg is ~75% of delivery time**, and late rates spiked to 12–19% after demand peaks (Black Friday, early 2018).
7. **Seller revenue is concentrated:** the top 10% of sellers = ~2/3 of revenue; 50 established sellers underperform, including the #2 seller by revenue.
""")
    st.subheader("Recommendations")
    st.markdown("""
- **Protect the delivery promise:** carrier capacity planning before peaks; fix routes to the North-East and Rio de Janeiro.
- **Lift average order value:** promote interest-free installments (7+ installment orders have ~3× AOV), bundles and free-shipping thresholds.
- **Win back high-value customers:** target the ~14k *At risk: big spenders*; time post-purchase journeys at 60–90 days.
- **Seller SLAs:** a handling-time target (e.g. ship within 2 days) and improvement plans for underperforming sellers.
""")
    st.info("Full analysis, SQL models and notebooks: "
            "[github.com/adhirajsinha1/olist-analytics](https://github.com/adhirajsinha1/olist-analytics)")
