import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from database import get_stats, get_all_predictions, get_all_patients

user      = st.session_state.user
doctor_id = user["id"]
stats     = get_stats(doctor_id)

st.title("🏠 Dashboard")
st.markdown(f"Welcome back, **Dr. {user['full_name']}** — here's your clinical overview.")
st.markdown("---")

# ── KPI cards ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.markdown(
    f'<div class="stat-card card-blue"><h2>{stats["patients"]}</h2><p>My Patients</p></div>',
    unsafe_allow_html=True,
)
c2.markdown(
    f'<div class="stat-card card-green"><h2>{stats["total"]}</h2><p>Predictions Made</p></div>',
    unsafe_allow_html=True,
)
c3.markdown(
    f'<div class="stat-card card-red"><h2>{stats["positive"]}</h2><p>Positive Cases</p></div>',
    unsafe_allow_html=True,
)
c4.markdown(
    f'<div class="stat-card card-cyan"><h2>{stats["negative"]}</h2><p>Negative Cases</p></div>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Recent predictions table  +  donut chart ──────────────────────────────────
left, right = st.columns([3, 2])

with left:
    st.subheader("📋 Recent Predictions")
    preds = get_all_predictions(doctor_id)
    if preds:
        df = pd.DataFrame(preds[:10])[["patient_name", "result", "confidence", "created_at"]]
        df.columns = ["Patient", "Result", "Confidence", "Date"]
        df["Result"]     = df["Result"].map({1: "🔴 Positive", 0: "🟢 Negative"})
        df["Confidence"] = df["Confidence"].apply(
            lambda x: f"{x:.1%}" if x is not None else "N/A"
        )
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No predictions yet. Start by adding patients and running predictions.")

with right:
    st.subheader("📊 Case Distribution")
    if stats["total"] > 0:
        fig = go.Figure(go.Pie(
            labels=["No Disease", "Heart Disease"],
            values=[stats["negative"], stats["positive"]],
            hole=0.45,
            marker_colors=["#4facfe", "#f5576c"],
            textinfo="label+percent",
        ))
        fig.update_layout(
            showlegend=True,
            height=280,
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No prediction data yet.")

# ── Patient growth over time ───────────────────────────────────────────────────
all_patients = get_all_patients(doctor_id)
if len(all_patients) > 1:
    st.markdown("---")
    st.subheader("📈 Patient Registrations Over Time")
    df_p = pd.DataFrame(all_patients)
    df_p["created_at"] = pd.to_datetime(df_p["created_at"])
    df_p["month"] = df_p["created_at"].dt.to_period("M").astype(str)
    monthly = df_p.groupby("month").size().reset_index(name="count")
    fig2 = px.bar(
        monthly, x="month", y="count",
        labels={"month": "Month", "count": "New Patients"},
        color_discrete_sequence=["#667eea"],
    )
    fig2.update_layout(height=300)
    st.plotly_chart(fig2, use_container_width=True)
