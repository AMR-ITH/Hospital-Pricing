import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Hospital Pricing Data Explorer", page_icon="🏥", layout="wide")
st.title("🏥 Hospital Pricing Data Explorer")
st.markdown("### Interactive analysis of hospital pricing and procedures")

@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    df_ = pd.read_csv(path)
    # Basic hygiene
    for c in ['hospital_name', 'payer_name', 'plan_name', 'description']:
        if c in df_.columns:
            df_[c] = df_[c].astype(str).fillna("Unknown")
    # Coerce numeric columns used in charts
    for c in ['estimated_amount', 'standard_charge|min', 'standard_charge|max']:
        if c in df_.columns:
            df_[c] = pd.to_numeric(df_[c], errors='coerce')
    return df_

try:
    df = load_csv('hospital_procedure_prices_detailed.csv')

    # =========================
    # Cascading sidebar filters
    # =========================
    st.sidebar.header("🔍 Filters")

    # 1) Hospital (single select)
    hospital_options = ["All"] + sorted(df['hospital_name'].dropna().unique().tolist())
    selected_hospital = st.sidebar.selectbox("Hospital", hospital_options, index=0)

    # Base frame after hospital for dynamic options
    base_after_hospital = df if selected_hospital == "All" else df[df['hospital_name'] == selected_hospital]

    # 2) Payer(s) for the chosen hospital (multiselect)
    payer_options = sorted(base_after_hospital['payer_name'].dropna().unique().tolist())
    selected_payers = st.sidebar.multiselect(
        "Payer(s)",
        options=payer_options,
        help="Leave empty to include all payers for the selected hospital."
    )

    # Base frame after hospital + payer(s)
    if selected_payers:
        base_after_payers = base_after_hospital[base_after_hospital['payer_name'].isin(selected_payers)]
    else:
        base_after_payers = base_after_hospital

    # 3) Plan(s) for the chosen hospital + payer(s) (multiselect)
    plan_options = sorted(base_after_payers['plan_name'].dropna().unique().tolist())
    selected_plans = st.sidebar.multiselect(
        "Plan(s)",
        options=plan_options,
        help="Leave empty to include all plans for the selection."
    )

    # Frame after hospital + payer(s) + plan(s) (used for range slider and initial metrics/plots)
    if selected_plans:
        base_after_plans = base_after_payers[base_after_payers['plan_name'].isin(selected_plans)]
    else:
        base_after_plans = base_after_payers

    # 4) Price range based on the current subset
    s = base_after_plans['estimated_amount'].dropna()
    if len(s) == 0:
        min_price, max_price = 0.0, 0.0
    else:
        min_price, max_price = float(s.min()), float(s.max())

    price_range = st.sidebar.slider(
        "Price Range ($)",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price),
        disabled=(min_price == max_price)
    )

    # Apply all filters to get final filtered_df
    filtered_df = base_after_plans[
        (base_after_plans['estimated_amount'] >= price_range[0]) &
        (base_after_plans['estimated_amount'] <= price_range[1])
    ].copy()

    # =========================
    # Key Metrics
    # =========================
    st.header("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", len(filtered_df))
    with col2:
        st.metric("Avg Price", f"${filtered_df['estimated_amount'].mean():,.2f}" if len(filtered_df) else "$0.00")
    with col3:
        st.metric("Min Price", f"${filtered_df['estimated_amount'].min():,.2f}" if len(filtered_df) else "$0.00")
    with col4:
        st.metric("Max Price", f"${filtered_df['estimated_amount'].max():,.2f}" if len(filtered_df) else "$0.00")

    # =========================
    # Tabs
    # =========================
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Overview", "💰 Price Analysis", "🏥 By Procedure", "🏢 By Payer"
    ])

    # -------- Overview --------
    with tab1:
        st.subheader("Price Distribution")
        if filtered_df.empty:
            st.info("No data for the current selection.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                fig_hist = px.histogram(
                    filtered_df,
                    x='estimated_amount',
                    nbins=30,
                    title='Distribution of Estimated Amounts',
                    labels={'estimated_amount': 'Estimated Amount ($)'}
                )
                fig_hist.update_layout(showlegend=False, xaxis_title="Estimated Amount ($)", yaxis_title="Count")
                fig_hist.update_xaxes(separatethousands=True)
                st.plotly_chart(fig_hist, use_container_width=True)

            with c2:
                fig_box = px.box(
                    filtered_df,
                    x='payer_name',
                    y='estimated_amount',
                    title='Price Distribution by Payer',
                    labels={'estimated_amount': 'Amount ($)', 'payer_name': 'Payer'},
                )
                fig_box.update_xaxes(tickangle=-45)
                st.plotly_chart(fig_box, use_container_width=True)

    # -------- Price Analysis --------
    with tab2:
        st.subheader("Detailed Price Analysis")
        if filtered_df.empty:
            st.info("No data for the current selection.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                    g = (
                        filtered_df.groupby(['plan_name', 'payer_name'], dropna=False)['estimated_amount']
                        .mean()
                        .reset_index(name='avg_price')
                    )
                    fig_plan = px.bar(
                        g,
                        x='avg_price',
                        y='plan_name',
                        color='payer_name',
                        barmode='group',  # grouped bars per plan
                        orientation='h',
                        title='Average Price by Plan and Payer',
                        labels={'avg_price': 'Average Amount ($)', 'plan_name': 'Plan', 'payer_name': 'Payer'}
                    )
                    st.plotly_chart(fig_plan, use_container_width=True)

            with c2:
                if {'standard_charge|max', 'standard_charge|min'}.issubset(filtered_df.columns):
                    filtered_df['price_variance'] = filtered_df['standard_charge|max'] - filtered_df['standard_charge|min']
                    top_variance = filtered_df.nlargest(10, 'price_variance')[['description', 'price_variance']]
                    fig_variance = px.bar(
                        top_variance,
                        x='price_variance',
                        y='description',
                        orientation='h',
                        title='Top 10 Procedures by Price Variance',
                        labels={'price_variance': 'Variance ($)', 'description': 'Procedure'}
                    )
                    st.plotly_chart(fig_variance, use_container_width=True)
                else:
                    st.info("Min/Max standard charge columns not found.")

            st.subheader("Min vs Max Standard Charges")
            if {'standard_charge|min', 'standard_charge|max'}.issubset(filtered_df.columns) and not filtered_df.empty:
                fig_scatter = px.scatter(
                    filtered_df,
                    x='standard_charge|min',
                    y='standard_charge|max',
                    color='payer_name',
                    hover_data=['description', 'estimated_amount'],
                    title='Relationship between Min and Max Charges',
                    labels={'standard_charge|min': 'Min Standard Charge ($)', 'standard_charge|max': 'Max Standard Charge ($)'}
                )
                xmin = filtered_df['standard_charge|min'].min()
                xmax = filtered_df['standard_charge|min'].max()
                fig_scatter.add_trace(
                    go.Scatter(
                        x=[xmin, xmax], y=[xmin, xmax],
                        mode='lines', name='Equal Line',
                        line=dict(dash='dash', color='gray')
                    )
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("Min/Max standard charge columns not found or no data.")

    # -------- By Procedure --------
    with tab3:
        st.subheader("Analysis by Procedure")
        if filtered_df.empty:
            st.info("No data for the current selection.")
        else:
            top_procedures = filtered_df.nlargest(10, 'estimated_amount')[['description', 'estimated_amount', 'payer_name', 'plan_name']]
            fig_top = px.bar(
                top_procedures,
                x='estimated_amount',
                y='description',
                color='payer_name',
                orientation='h',
                title='Top 10 Most Expensive Procedures',
                labels={'estimated_amount': 'Amount ($)', 'description': 'Procedure'}
            )
            st.plotly_chart(fig_top, use_container_width=True)

            st.subheader("Most Common Procedures")
            procedure_counts = filtered_df['description'].value_counts().head(10)
            fig_freq = px.bar(
                x=procedure_counts.values,
                y=procedure_counts.index,
                orientation='h',
                title='Top 10 Most Common Procedures',
                labels={'x': 'Count', 'y': 'Procedure'}
            )
            st.plotly_chart(fig_freq, use_container_width=True)

    # -------- By Payer --------
    with tab4:
        st.subheader("Payer Analysis")
        if filtered_df.empty:
            st.info("No data for the current selection.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                payer_stats = filtered_df.groupby('payer_name', dropna=False).agg({'estimated_amount': ['mean', 'count']}).round(2)
                payer_stats.columns = ['Avg Amount', 'Count']
                payer_stats = payer_stats.sort_values('Avg Amount', ascending=False)
                fig_payer = px.bar(
                    x=payer_stats['Avg Amount'],
                    y=payer_stats.index,
                    orientation='h',
                    title='Average Amount by Payer',
                    labels={'x': 'Average Amount ($)', 'y': 'Payer'}
                )
                fig_payer.update_layout(width=512, height=620)
                st.plotly_chart(fig_payer, use_container_width=True)
            with c2:
                top_n = st.number_input("Show top N payers", min_value=5, max_value=30, value=12, step=1)
                chart_type = st.radio("Chart type", ["Donut", "Bar"], index=0, horizontal=True)

                # Counts
                payer_counts = filtered_df['payer_name'].value_counts(dropna=False)
                total = int(payer_counts.sum())

                # Top N + Other
                top_counts = payer_counts.head(top_n)
                other = total - int(top_counts.sum())

                data = top_counts.reset_index()
                data.columns = ["payer_name", "count"]
                if other > 0:
                    data = pd.concat([data, pd.DataFrame([{"payer_name": "Other", "count": other}])], ignore_index=True)
                data["share"] = data["count"] / total

                if chart_type == "Donut":
                    fig_pie = px.pie(
                        data,
                        values="count",
                        names="payer_name",
                        hole=0.4,
                        title="Distribution of Records by Payer (top N + Other)"
                    )
                    fig_pie.update_traces(
                        textposition="inside",
                        texttemplate="%{label}<br>%{percent:.1%}",
                        hovertemplate="Payer: %{label}<br>Records: %{value:,}<br>Share: %{percent:.1%}<extra></extra>",
                        pull=[0.02] * (len(data) - 1) + [0]  # subtle separation
                    )
                    fig_pie.update_layout(margin=dict(t=60, b=20, l=20, r=20), showlegend=True)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    fig_bar = px.bar(
                        data.sort_values("count", ascending=True),
                        x="count",
                        y="payer_name",
                        orientation="h",
                        title="Records by Payer (top N + Other)",
                        labels={"count": "Records", "payer_name": "Payer"},
                        text=data.sort_values("count", ascending=True)["share"].map(lambda v: f"{v:.1%}")
                    )
                    fig_bar.update_traces(textposition="outside", cliponaxis=False)
                    fig_bar.update_layout(margin=dict(t=60, b=20, l=20, r=20))
                    st.plotly_chart(fig_bar, use_container_width=True)

            st.subheader("Detailed Payer Statistics")
            payer_detailed = filtered_df.groupby('payer_name', dropna=False).agg({
                'estimated_amount': ['mean', 'median', 'min', 'max', 'count']
            }).round(2)
            payer_detailed.columns = ['Avg Amount', 'Median', 'Min', 'Max', 'Count']
            st.dataframe(payer_detailed, use_container_width=True)


except FileNotFoundError:
    st.error("❌ Error: 'hospital_procedure_prices_detailed.csv' not found in the current directory.")
    st.info("Please make sure the CSV file is in the same directory as this script.")
    st.stop()
except Exception as e:
    st.error(f"❌ Error loading data: {str(e)}")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("Hospital Pricing Data Explorer v1.0")