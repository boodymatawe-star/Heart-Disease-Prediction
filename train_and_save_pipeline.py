import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib

# Load your cleaned dataset
df = pd.read_csv("cleaned_heart_data.csv")

# Features and target (adjust column names as needed)
X = df.drop("num", axis=1)
y = df["num"]

# Split data (optional, for validation)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Example pipeline (adjust as needed)
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", RandomForestClassifier(random_state=42))
])

# Train pipeline
pipeline.fit(X_train, y_train)

# Save pipeline
joblib.dump(pipeline, "final_pipeline.pkl")
print("Pipeline saved as final_pipeline.pkl")