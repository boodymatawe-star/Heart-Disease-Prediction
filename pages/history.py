import json

import pandas as pd
import plotly.express as px
import streamlit as st

from database import get_all_patients, get_all_predictions, get_patient_predictions

user      = st.session_state.user
doctor_id = user["id"]

st.title("📋 Prediction History")
st.markdown("---")

# ── Filters ────────────────────────────────────────────────────────────────────
patients = get_all_patients(doctor_id)
patient_options: dict[str, int | None] = {"All Patients": None}
patient_options.update({p["full_name"]: p["id"] for p in patients})

f1, f2, f3 = st.columns(3)
with f1:
    patient_filter = st.selectbox("Filter by Patient", list(patient_options.keys()))
with f2:
    result_filter = st.selectbox("Filter by Result", ["All", "Positive", "Negative"])
with f3:
    sort_order = st.selectbox("Sort by Date", ["Newest First", "Oldest First"])

selected_pid = patient_options[patient_filter]

if selected_pid:
    preds = get_patient_predictions(selected_pid)
else:
    preds = get_all_predictions(doctor_id)

# Apply result filter
if result_filter == "Positive":
    preds = [p for p in preds if p["result"] == 1]
elif result_filter == "Negative":
    preds = [p for p in preds if p["result"] == 0]

# Apply sort
if sort_order == "Oldest First":
    preds = list(reversed(preds))

if not preds:
    st.info("No prediction records match the selected filters.")
    st.stop()

# ── Summary metrics ────────────────────────────────────────────────────────────
total    = len(preds)
positive = sum(1 for p in preds if p["result"] == 1)
negative = total - positive

m1, m2, m3 = st.columns(3)
m1.metric("Total Records",   total)
m2.metric("Positive Cases",  positive)
m3.metric("Negative Cases",  negative)

st.markdown(f"**{total} record(s) shown**")
st.markdown("---")

# ── Record list ────────────────────────────────────────────────────────────────
for pred in preds:
    result_icon = "🔴" if pred["result"] == 1 else "🟢"
    result_text = "Positive" if pred["result"] == 1 else "Negative"
    conf_str    = f"{pred['confidence']:.1%}" if pred.get("confidence") is not None else "N/A"
    patient_lbl = pred.get("patient_name", "Unknown Patient")
    date_str    = (pred.get("created_at") or "")[:16]

    header = f"{result_icon} {result_text}  —  {patient_lbl}  |  {date_str}  |  Confidence: {conf_str}"

    with st.expander(header):
        left, right = st.columns(2)

        with left:
            st.markdown(f"**Patient:** {patient_lbl}")
            st.markdown(f"**Doctor:** Dr. {pred.get('doctor_name', 'N/A')}")
            st.markdown(f"**Date & Time:** {date_str}")
            st.markdown(f"**Result:** {result_icon} {result_text}")
            st.markdown(f"**Model Confidence:** {conf_str}")
            notes = pred.get("clinical_notes") or ""
            if notes.strip():
                st.markdown(f"**Clinical Notes:** {notes}")

        with right:
            if pred.get("input_features"):
                try:
                    features = json.loads(pred["input_features"])
                    feat_df  = pd.DataFrame(
                        {"Feature": features.keys(), "Value": features.values()}
                    )
                    fig = px.bar(
                        feat_df, x="Feature", y="Value",
                        color="Value",
                        color_continuous_scale="RdYlGn_r",
                        title="Feature Snapshot",
                    )
                    fig.update_layout(
                        height=240, showlegend=False,
                        margin=dict(t=30, b=0, l=0, r=0),
                        xaxis_tickangle=-40,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except (json.JSONDecodeError, Exception):
                    st.caption("Could not parse feature data.")

# ── Trend chart ────────────────────────────────────────────────────────────────
if len(preds) >= 2:
    st.markdown("---")
    st.subheader("📈 Prediction Confidence Over Time")

    df_trend = pd.DataFrame(preds)
    df_trend["created_at"]   = pd.to_datetime(df_trend["created_at"])
    df_trend["result_label"] = df_trend["result"].map({1: "Positive", 0: "Negative"})

    fig = px.scatter(
        df_trend,
        x="created_at",
        y="confidence",
        color="result_label",
        symbol="result_label",
        size_max=12,
        color_discrete_map={"Positive": "#f5576c", "Negative": "#4facfe"},
        hover_data={"patient_name": True} if "patient_name" in df_trend.columns else {},
        labels={
            "created_at":   "Date",
            "confidence":   "Confidence",
            "result_label": "Result",
        },
        title="Confidence Over Time by Result",
    )
    fig.update_traces(marker_size=10)
    fig.update_layout(height=380, yaxis_tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)
