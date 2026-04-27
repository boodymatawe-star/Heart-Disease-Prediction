from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import streamlit as st

from database import get_all_predictions, get_stats

user      = st.session_state.user
doctor_id = user["id"]

st.title("📊 Analytics")
st.markdown("---")

tab_dataset, tab_personal = st.tabs(["📁  Dataset Insights", "🩺  My Predictions"])


# ── Tab 1: Dataset Insights ────────────────────────────────────────────────────
with tab_dataset:
    data_path = Path(__file__).parent.parent / "cleaned_heart_data.csv"
    if not data_path.exists():
        st.warning("`cleaned_heart_data.csv` not found. Run the preprocessing notebook first.")
        st.stop()

    heart_df = pd.read_csv(data_path)
    if "num" in heart_df.columns:
        heart_df["num"] = heart_df["num"].astype(int)

    numeric_cols = heart_df.select_dtypes(include="number").columns.tolist()

    st.subheader("Dataset Overview")
    st.markdown(
        f"**{len(heart_df):,} records** &nbsp;|&nbsp; "
        f"**{len(heart_df.columns)} features** &nbsp;|&nbsp; "
        f"**Positive rate: {heart_df['num'].mean():.1%}**"
    )

    # Row 1
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        counts = heart_df["num"].value_counts().reset_index()
        counts.columns = ["Diagnosis", "Count"]
        counts["Diagnosis"] = counts["Diagnosis"].map({0: "No Disease", 1: "Heart Disease"})
        fig = px.pie(
            counts, values="Count", names="Diagnosis",
            color_discrete_sequence=["#4facfe", "#f5576c"],
            title="Disease Distribution",
            hole=0.4,
        )
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)

    with r1c2:
        fig = px.histogram(
            heart_df, x="age", color="num", barmode="overlay",
            color_discrete_map={0: "#4facfe", 1: "#f5576c"},
            labels={"num": "Diagnosis", "age": "Age"},
            title="Age Distribution by Diagnosis",
            nbins=25,
        )
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)

    # Row 2
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        fig = px.box(
            heart_df, x="num", y="chol", color="num",
            color_discrete_map={0: "#4facfe", 1: "#f5576c"},
            labels={"num": "Diagnosis (0=No, 1=Yes)", "chol": "Cholesterol (mg/dl)"},
            title="Cholesterol by Diagnosis",
        )
        fig.update_layout(height=320, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with r2c2:
        fig = px.box(
            heart_df, x="num", y="thalch", color="num",
            color_discrete_map={0: "#4facfe", 1: "#f5576c"},
            labels={"num": "Diagnosis (0=No, 1=Yes)", "thalch": "Max Heart Rate"},
            title="Max Heart Rate by Diagnosis",
        )
        fig.update_layout(height=320, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Correlation heatmap
    st.subheader("Feature Correlation Heatmap")
    corr = heart_df[numeric_cols].corr()
    fig_heat, ax = plt.subplots(figsize=(11, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax, linewidths=0.4)
    ax.set_title("Pearson Correlation Matrix", fontsize=13)
    st.pyplot(fig_heat, use_container_width=True)

    # Interactive violin
    st.subheader("Interactive Feature Explorer")
    feat = st.selectbox("Select feature to compare against diagnosis", [c for c in numeric_cols if c != "num"])
    fig = px.violin(
        heart_df, x="num", y=feat, box=True, points="outliers", color="num",
        color_discrete_map={0: "#4facfe", 1: "#f5576c"},
        labels={"num": "Diagnosis (0=No, 1=Yes)"},
        title=f"{feat} by Diagnosis",
    )
    fig.update_layout(height=380, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


# ── Tab 2: My Predictions ──────────────────────────────────────────────────────
with tab_personal:
    st.subheader("My Prediction Statistics")
    preds = get_all_predictions(doctor_id)

    if not preds:
        st.info("No predictions yet — run your first prediction to see analytics here.")
        st.stop()

    df = pd.DataFrame(preds)
    df["created_at"]   = pd.to_datetime(df["created_at"])
    df["date"]         = df["created_at"].dt.date
    df["month"]        = df["created_at"].dt.to_period("M").astype(str)
    df["result_label"] = df["result"].map({1: "Positive", 0: "Negative"})

    # KPI row
    stats = get_stats(doctor_id)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Predictions", stats["total"])
    k2.metric("Positive",          stats["positive"])
    k3.metric("Negative",          stats["negative"])
    positive_rate = stats["positive"] / stats["total"] if stats["total"] else 0
    k4.metric("Positive Rate",     f"{positive_rate:.1%}")

    st.markdown("---")

    # Row A
    a1, a2 = st.columns(2)
    with a1:
        counts = df["result_label"].value_counts().reset_index()
        counts.columns = ["Result", "Count"]
        fig = px.pie(
            counts, values="Count", names="Result",
            color_discrete_map={"Positive": "#f5576c", "Negative": "#4facfe"},
            title="My Case Distribution",
            hole=0.4,
        )
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)

    with a2:
        daily = df.groupby(["date", "result_label"]).size().reset_index(name="count")
        fig = px.bar(
            daily, x="date", y="count", color="result_label",
            color_discrete_map={"Positive": "#f5576c", "Negative": "#4facfe"},
            barmode="stack",
            labels={"date": "Date", "count": "Predictions", "result_label": "Result"},
            title="Daily Predictions",
        )
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)

    # Row B
    b1, b2 = st.columns(2)
    with b1:
        avg_conf = df.groupby("result_label")["confidence"].mean().reset_index()
        avg_conf.columns = ["Result", "Avg Confidence"]
        fig = px.bar(
            avg_conf, x="Result", y="Avg Confidence", color="Result",
            color_discrete_map={"Positive": "#f5576c", "Negative": "#4facfe"},
            title="Average Confidence by Result",
        )
        fig.update_layout(height=320, showlegend=False, yaxis_tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

    with b2:
        if len(df) >= 2:
            fig = px.scatter(
                df, x="created_at", y="confidence",
                color="result_label",
                color_discrete_map={"Positive": "#f5576c", "Negative": "#4facfe"},
                title="Confidence Over Time",
                labels={"created_at": "Date", "confidence": "Confidence", "result_label": "Result"},
            )
            fig.update_layout(height=320, yaxis_tickformat=".0%")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Make more predictions to see this chart.")
