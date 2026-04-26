# 🩺 Heart Disease Prediction Project

A machine learning project to predict heart disease using the UCI Heart Disease dataset.  
The project includes data preprocessing, feature selection, PCA, supervised and unsupervised learning, hyperparameter tuning, and a Streamlit UI for predictions.

---

## 📂 Project Structure

Heart_Disease_Project/
│── data/
│ ├── heart_disease_uci.csv
│── notebooks/
│ ├── 01_data_preprocessing.ipynb
│ ├── 02_pca_analysis.ipynb
│ ├── 03_feature_selection.ipynb
│ ├── 04_supervised_learning.ipynb
│ ├── 05_unsupervised_learning.ipynb
│ ├── 06_hyperparameter_tuning.ipynb
│── models/
│ ├── final_model.pkl
│── ui/
│ ├── app.py # Streamlit UI
│── deployment/
│ ├── ngrok_setup.txt
│── results/
│ ├── evaluation_metrics.txt
│── README.md
│── requirements.txt
│── .gitignore

---

## ⚙️ Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Mohanad-Elkhodary/Heart_Disease_Project.git
cd Heart_Disease_Project
pip install -r requirements.txt
```

🚀 Running the Streamlit App

Run the app locally:

```
streamlit run ui/app.py
```

The app will open in your browser at `http://localhost:8501`
.
🌍 Public Access with Ngrok

To share your app publicly:

1. Install Ngrok

2. Authenticate with your authtoken (instructions in deployment/ngrok_setup.txt).

3. Run: ngrok http 8501

4.Share the generated public URL.

📊 Results

See detailed evaluation metrics in results/evaluation_metrics.txt.

Final Random Forest Accuracy: 0.86

Confusion Matrix:
[[62 13]
 [13 96]]
Classification Report:
precision recall f1-score support
0 0.83 0.83 0.83 75
1 0.88 0.88 0.88 109
accuracy 0.86 184
macro avg 0.85 0.85 0.85 184
weighted avg 0.86 0.86 0.86 184

👨‍💻 Author

Developed by **Ezzeldean Ahmed**  
as part of the _Sprints AI & Machine Learning Program_.
