import json
from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st

from database import create_patient, get_all_patients, save_prediction

user      = st.session_state.user
doctor_id = user["id"]


# ── Load model (cached across reruns) ─────────────────────────────────────────
@st.cache_resource
def _load_pipeline():
    path = Path(__file__).parent.parent / "final_pipeline.pkl"
    return joblib.load(str(path))


try:
    pipeline = _load_pipeline()
except FileNotFoundError:
    st.error(
        "**Model file not found.**  "
        "Run `train_and_save_pipeline.py` (or notebook 06) first to generate `final_pipeline.pkl`."
    )
    st.stop()


# ── Page header ───────────────────────────────────────────────────────────────
st.title("🔬 New Prediction")
st.markdown("Select a patient, fill in the clinical measurements, and run the model.")
st.markdown("---")

# ── Patient selection ─────────────────────────────────────────────────────────
patients = get_all_patients(doctor_id)
patient_map: dict[str, dict] = {
    f"{p['full_name']}  (NID: {p['national_id'] or p['id']})": p
    for p in patients
}

sel_col, btn_col = st.columns([4, 1])
with sel_col:
    choice = st.selectbox(
        "Select Patient",
        ["— choose a patient —"] + list(patient_map.keys()),
    )
with btn_col:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Quick-add", use_container_width=True):
        st.session_state["show_quick_add"] = True

selected_patient = patient_map.get(choice)
if selected_patient:
    info = (
        f"**{selected_patient['full_name']}** &nbsp;|&nbsp; "
        f"DOB: {selected_patient.get('date_of_birth') or 'N/A'} &nbsp;|&nbsp; "
        f"Gender: {selected_patient.get('gender') or 'N/A'} &nbsp;|&nbsp; "
        f"Phone: {selected_patient.get('phone') or 'N/A'}"
    )
    st.info(info)

# Quick-add patient inline form
if st.session_state.get("show_quick_add"):
    with st.expander("➕ Quick-add New Patient", expanded=True):
        with st.form("quick_add_form", clear_on_submit=True):
            qa1, qa2 = st.columns(2)
            with qa1:
                qa_name   = st.text_input("Full Name *")
                qa_nid    = st.text_input("National ID")
                qa_gender = st.selectbox("Gender", ["Male", "Female"])
            with qa2:
                qa_dob   = st.date_input("Date of Birth")
                qa_phone = st.text_input("Phone")
            if st.form_submit_button("Register & Select", type="primary"):
                if not qa_name:
                    st.error("Full name is required.")
                else:
                    pid, err = create_patient(
                        qa_nid or None, qa_name, str(qa_dob), qa_gender,
                        qa_phone, "", "", "", "", doctor_id,
                    )
                    if err:
                        st.error(err)
                    else:
                        st.success(f"Patient '{qa_name}' registered (ID: {pid}).")
                        st.session_state["show_quick_add"] = False
                        st.rerun()

st.markdown("---")

# ── Clinical measurements form ────────────────────────────────────────────────
st.subheader("🩺 Clinical Measurements")
with st.form("prediction_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Demographics & Vitals**")
        age      = st.number_input("Age (years)",                        18, 100, 50)
        sex      = st.selectbox("Sex", ["Male", "Female"])
        trestbps = st.number_input("Resting Blood Pressure (mm Hg)",    80, 220, 120)
        chol     = st.number_input("Serum Cholesterol (mg/dl)",        100, 700, 200)
        fbs      = st.radio("Fasting Blood Sugar > 120 mg/dl", ["No", "Yes"], horizontal=True)

    with col2:
        st.markdown("**Cardiac Tests**")
        thalch  = st.number_input("Max Heart Rate Achieved (bpm)",  50, 220, 150)
        oldpeak = st.number_input("ST Depression (Oldpeak)",       0.0, 8.0, 1.0, step=0.1)
        exang   = st.radio("Exercise Induced Angina",              ["No", "Yes"], horizontal=True)
        restecg = st.selectbox(
            "Resting ECG Results",
            ["Normal", "ST-T Abnormality"],
        )

    with col3:
        st.markdown("**Chest Pain & ST Slope**")
        cp = st.selectbox(
            "Chest Pain Type",
            ["Asymptomatic", "Non-Anginal", "Typical Angina", "Atypical Angina"],
        )
        slope = st.selectbox(
            "ST Segment Slope (peak exercise)",
            ["Flat", "Upsloping"],
        )
        st.markdown("<br>", unsafe_allow_html=True)
        clinical_notes = st.text_area(
            "Clinical Notes (optional)",
            placeholder="Additional observations, medication, context…",
            height=110,
        )

    run_btn = st.form_submit_button(
        "🔮 Run Prediction", use_container_width=True, type="primary"
    )

# ── Handle prediction ─────────────────────────────────────────────────────────
if run_btn:
    if not selected_patient:
        st.warning("⚠️ Please select or add a patient before running a prediction.")
        st.stop()

    # Encode categorical inputs
    input_data = pd.DataFrame([{
        "age":                      age,
        "trestbps":                 trestbps,
        "sex_Male":                 1 if sex == "Male" else 0,
        "chol":                     chol,
        "thalch":                   thalch,
        "oldpeak":                  oldpeak,
        "exang":                    1 if exang == "Yes" else 0,
        "cp_non-anginal":           1 if cp == "Non-Anginal" else 0,
        "cp_typical angina":        1 if cp == "Typical Angina" else 0,
        "cp_atypical angina":       1 if cp == "Atypical Angina" else 0,
        "restecg_normal":           1 if restecg == "Normal" else 0,
        "restecg_st-t abnormality": 1 if restecg == "ST-T Abnormality" else 0,
        "slope_upsloping":          1 if slope == "Upsloping" else 0,
        "slope_flat":               1 if slope == "Flat" else 0,
        "fbs":                      1 if fbs == "Yes" else 0,
    }])

    # Align to model's expected feature order
    input_data = input_data[pipeline.feature_names_in_]

    prediction  = int(pipeline.predict(input_data)[0])
    proba       = pipeline.predict_proba(input_data)[0]
    confidence  = float(proba[prediction])

    # ── Result display ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Prediction Result")

    res_col, conf_col = st.columns([2, 1])
    with res_col:
        if prediction == 1:
            st.markdown(
                '<div class="result-positive">'
                '<h2>🚨 Heart Disease Detected</h2>'
                '<p>The model predicts a <strong>positive</strong> risk of heart disease.</p>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="result-negative">'
                '<h2>💚 No Heart Disease Detected</h2>'
                '<p>The model predicts <strong>no significant</strong> heart disease risk.</p>'
                '</div>',
                unsafe_allow_html=True,
            )

    with conf_col:
        st.metric("Model Confidence", f"{confidence:.1%}")
        st.metric("Risk Level", "🔴 HIGH" if prediction == 1 else "🟢 LOW")
        disease_prob = float(proba[1])
        st.metric("Disease Probability", f"{disease_prob:.1%}")

    # ── Feature bar chart ──────────────────────────────────────────────────────
    feat_df = pd.DataFrame({
        "Feature": pipeline.feature_names_in_,
        "Value":   input_data.iloc[0].values,
    })
    fig = px.bar(
        feat_df, x="Feature", y="Value",
        title="Patient Input Feature Values",
        color="Value",
        color_continuous_scale="RdYlGn_r",
    )
    fig.update_layout(height=360, showlegend=False, xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

    # ── Probability gauge ──────────────────────────────────────────────────────
    import plotly.graph_objects as go
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=round(disease_prob * 100, 1),
        title={"text": "Heart Disease Probability (%)"},
        delta={"reference": 50},
        gauge={
            "axis": {"range": [0, 100]},
            "bar":  {"color": "#f5576c" if prediction == 1 else "#43e97b"},
            "steps": [
                {"range": [0,  40], "color": "#d4edda"},
                {"range": [40, 60], "color": "#fff3cd"},
                {"range": [60, 100], "color": "#f8d7da"},
            ],
            "threshold": {
                "line":  {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": 50,
            },
        },
    ))
    fig_gauge.update_layout(height=280)
    st.plotly_chart(fig_gauge, use_container_width=True)

    # ── Persist to database ────────────────────────────────────────────────────
    pred_id = save_prediction(
        patient_id=selected_patient["id"],
        doctor_id=doctor_id,
        result=prediction,
        confidence=confidence,
        input_features_json=json.dumps(input_data.iloc[0].to_dict()),
        clinical_notes=clinical_notes,
    )
    st.success(f"✅ Prediction saved to patient record (Prediction ID: {pred_id}).")
