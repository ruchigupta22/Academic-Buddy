"""
explain_predictions.py
------------------------
Uses SHAP (TreeExplainer, since our model is a Random Forest) to explain
WHY each topic was predicted as high-yield or low-yield for the latest year,
rather than just showing a raw probability.
"""

import pickle
import pandas as pd
import shap
import matplotlib.pyplot as plt
from train_topic_predictor import load_raw_questions, build_features

with open("topic_predictor_model.pkl", "rb") as f:
    saved = pickle.load(f)

model = saved["model"]
feature_cols = saved["feature_cols"]

df = load_raw_questions()
feat_df = build_features(df)

latest_year = feat_df["year"].max()
latest = feat_df[feat_df["year"] == latest_year].reset_index(drop=True)
X_latest = latest[feature_cols]

# TreeExplainer is the efficient, exact SHAP method for tree-based models
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_latest)

# For binary classification, shap_values is a list [class_0_values, class_1_values]
# We care about class 1 (topic appears)
if isinstance(shap_values, list):
    shap_vals_positive = shap_values[1]
else:
    shap_vals_positive = shap_values[:, :, 1] if shap_values.ndim == 3 else shap_values

print(f"=== SHAP explanations for {latest_year} predictions ===\n")

for i, row in latest.iterrows():
    topic = row["topic"]
    prob = model.predict_proba(X_latest.iloc[[i]])[0][1]

    # Get feature contributions for this specific topic
    contributions = pd.Series(shap_vals_positive[i], index=feature_cols).sort_values(key=abs, ascending=False)

    print(f"{topic} — predicted probability: {prob:.3f} (actually appeared: {bool(row['appeared_this_year'])})")
    print("  Top factors:")
    for feat, val in contributions.head(3).items():
        direction = "increased" if val > 0 else "decreased"
        print(f"    - {feat} = {row[feat]:.2f} → {direction} prediction by {abs(val):.3f}")
    print()

# Save a summary plot showing overall feature importance across all topics
plt.figure()
shap.summary_plot(shap_vals_positive, X_latest, feature_names=feature_cols, show=False)
plt.tight_layout()
plt.savefig("shap_summary_plot.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: shap_summary_plot.png")