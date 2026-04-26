import streamlit as st
import joblib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
#load the pipeline(model)
pipeline = joblib.load("final_pipeline.pkl")
st.title("❤️ Heart Disease Prediction App")
st.write("Enter patient details below to predict the risk of heart disease.")
#User Inputs
age = st.number_input("Age", 20, 100, 50)

### ADDED: Input for trestbps (Resting Blood Pressure) ###
trestbps = st.number_input("Resting Blood Pressure (mm Hg)", 90, 200, 120)

sex = st.selectbox("Sex", ["Male", "Female"])
chol = st.number_input("Cholesterol (mg/dl)", 100, 600, 200)
thalch = st.number_input("Max Heart Rate Achieved", 50, 220, 150)
oldpeak = st.number_input("ST depression (Oldpeak)", 0.0, 6.0, 1.0)
exang = st.selectbox("Exercise Induced Angina", ["No", "Yes"])
fbs = st.radio("Fasting Blood Sugar > 120 mg/dl", ["Yes", "No"])

# One-hot encoded features from original script
cp_non_anginal = st.checkbox("Chest Pain: Non-Anginal")
cp_typical_angina = st.checkbox("Chest Pain: Typical Angina")
cp_atypical_angina = st.checkbox("Chest Pain: Atypical Angina")
abnormality = st.checkbox("Resting ECG: ST-T Abnormality")
slope_unsloping = st.checkbox("Slope: Upsloping")




### MODIFIED: Combined selection for restecg and slope to correctly generate ALL required one-hot columns ###

# Handle Restecg (Must generate 'restecg_normal' and 'restecg_st-t abnormality' from a single input)
restecg_option = st.selectbox(
    "Resting Electrocardiographic Results (Restecg)",
    ["Normal", "ST-T Abnormality"] # Assuming the third category 'left ventricular hypertrophy' was dropped or is not needed
)
# Handle Slope (Must generate 'slope_upsloping' and 'slope_flat' from a single input)
slope_option = st.selectbox(
    "Slope of the peak exercise ST segment",
    ["Upsloping", "Flat"] # Assuming the third category 'downsloping' was dropped or is not needed
)

# one-hot encode
sex_male = 1 if sex == "Male" else 0
exang_val = 1 if exang == "Yes" else 0
fbs_val = 1 if fbs == "Yes" else 0 # Renamed 'fbs' variable to 'fbs_val' to avoid conflict with the input variable

# Chest Pain
cp_non_anginal_val = 1 if cp_non_anginal else 0
cp_typical_angina_val = 1 if cp_typical_angina else 0
cp_atypical_angina_val = 1 if cp_atypical_angina else 0

# Restecg
restecg_st_t_abnormality = 1 if restecg_option == "ST-T Abnormality" else 0
### ADDED: restecg_normal ###
restecg_normal = 1 if restecg_option == "Normal" else 0

# Slope
slope_upsloping_val = 1 if slope_option == "Upsloping" else 0
### ADDED: slope_flat ###
slope_flat_val = 1 if slope_option == "Flat" else 0


# build input dataframe
# Ensure input_data columns are in the same order as during training
# build input dataframe
input_data = pd.DataFrame([{
    "age": age,
    "trestbps": trestbps,
    "sex_Male": sex_male,
    "chol": chol,
    "thalch": thalch,
    "oldpeak": oldpeak,
    "exang": exang_val,
    "cp_non-anginal": cp_non_anginal_val,
    "cp_typical angina": cp_typical_angina_val,
    "cp_atypical angina": cp_atypical_angina_val,
    "restecg_normal": restecg_normal,
    "restecg_st-t abnormality": restecg_st_t_abnormality,
    "slope_upsloping": slope_upsloping_val,
    "slope_flat": slope_flat_val,
    "fbs": fbs_val
}])

# Ensure input_data columns are in the same order as during training
feature_order = pipeline.feature_names_in_
input_data = input_data[feature_order]
if st.button("Predict"):
    prediction = pipeline.predict(input_data)[0]

    if prediction == 1:
        st.error("🚨 Prediction Result 🚨")
        st.markdown(
            "<h2 style='text-align: center; color: red;'>Heart Disease Detected</h2>",
            unsafe_allow_html=True
        )
    else:
        st.success("💚 Prediction Result 💚")
        st.markdown(
            "<h2 style='text-align: center; color: green;'>No Heart Disease</h2>",
            unsafe_allow_html=True
        )


# Example visualization
st.subheader("Heart Disease Data Visualization")

# Suppose input_data is your DataFrame with one row
df = pd.DataFrame({
    "Feature": input_data.columns,
    "Value": input_data.iloc[0].values
})

fig = px.bar(df, x="Feature", y="Value", title="User Input Features")
st.plotly_chart(fig, use_container_width=True)
st.subheader("📊 Explore Heart Disease Trends")

# Load your cleaned dataset (the one you trained your model on)
# Note: You need to have 'cleaned_heart_data.csv' in the same directory for this part to work.
try:
    heart_df = pd.read_csv("cleaned_heart_data.csv")  # make sure this file has the 'num' column

    # 1. Distribution of target variable
    st.write("### Heart Disease Distribution")
    fig, ax = plt.subplots()
    sns.countplot(x="num", data=heart_df, ax=ax, palette="coolwarm")
    ax.set_title("Heart Disease Cases (0 = No, 1 = Yes)")
    st.pyplot(fig)

    # 2. Age vs. Heart Disease
    st.write("### Age vs Heart Disease")
    fig, ax = plt.subplots()
    sns.histplot(data=heart_df, x="age", hue="num", multiple="stack", bins=20, ax=ax)
    ax.set_title("Age Distribution by Heart Disease")
    st.pyplot(fig)

    # 3. Cholesterol vs Heart Disease
    st.write("### Cholesterol Levels by Heart Disease")
    fig, ax = plt.subplots()
    sns.boxplot(x="num", y="chol", data=heart_df, ax=ax, palette="Set2")
    ax.set_title("Cholesterol Levels (by Diagnosis)")
    st.pyplot(fig)

    # 4. Interactive Feature Correlation
    st.write("### Feature Correlation Heatmap")
    fig, ax = plt.subplots(figsize=(8,6))
    # Ensure 'num' is an integer for correlation in case it's loaded as float
    if 'num' in heart_df.columns:
        heart_df['num'] = heart_df['num'].astype(int)
    sns.heatmap(heart_df.corr(numeric_only=True), annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
    st.pyplot(fig)

    feature = st.selectbox("Choose feature to compare with target", ["age", "chol", "thalch", "oldpeak"])
    fig, ax = plt.subplots()
    sns.boxplot(x="num", y=feature, data=heart_df, ax=ax)
    st.pyplot(fig)
except FileNotFoundError:
    st.warning("Could not load 'cleaned_heart_data.csv'. Visualizations requiring the full dataset are disabled.")