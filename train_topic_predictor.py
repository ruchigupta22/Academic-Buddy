"""
train_topic_predictor.py
--------------------------
Predicts whether a topic will appear in the NEXT year's exam, using only
data available up to the prior year (avoids look-ahead leakage).

Framing: for each (topic, year) pair, using only years strictly BEFORE
that year as history, engineer features describing the topic's pattern
so far, then label whether it actually appeared in that year.

Evaluation: leave-one-year-out temporal validation (train on all years
before year Y, test on year Y) - NOT a random split, since a random split
would let the model see "future" years during training.
"""

import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score
from backend.db.sql_client import get_db

COURSE_CODE = "MT301"

def load_raw_questions():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT topic, year, marks, difficulty, question_type
            FROM pyq_questions
            WHERE course_code = ?
            ORDER BY year
        """, (COURSE_CODE,)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def build_features(df):
    """
    For every (topic, year) combination where the topic has ANY history
    before that year, build features from years strictly before `year`.
    """
    all_years = sorted(df["year"].unique())
    all_topics = df["topic"].unique()
    difficulty_map = {"Easy": 1, "Medium": 2, "Hard": 3}

    records = []
    for year in all_years[1:]:  # skip first year, no history exists before it
        prior = df[df["year"] < year]
        if prior.empty:
            continue
        for topic in all_topics:
            topic_hist = prior[prior["topic"] == topic]

            appeared_this_year = int(((df["year"] == year) & (df["topic"] == topic)).any())

            years_seen = sorted(topic_hist["year"].unique())
            n_prior_years = len(years_seen)
            total_appearances = len(topic_hist)

            # Recency-weighted score: appearances in more recent years count more
            if n_prior_years > 0:
                recency_weights = [1 / (year - y) for y in years_seen]
                recency_score = sum(recency_weights)
                years_since_last = year - max(years_seen)
                avg_marks = topic_hist["marks"].mean()
                avg_difficulty = topic_hist["difficulty"].map(difficulty_map).mean()
                appearance_rate = n_prior_years / len(all_years[:list(all_years).index(year)])
            else:
                recency_score = 0
                years_since_last = 99  # never seen -> large "gap"
                avg_marks = 0
                avg_difficulty = 0
                appearance_rate = 0

            records.append({
                "topic": topic,
                "year": year,
                "total_appearances": total_appearances,
                "n_prior_years": n_prior_years,
                "recency_score": recency_score,
                "years_since_last": years_since_last,
                "avg_marks": avg_marks,
                "avg_difficulty": avg_difficulty,
                "appearance_rate": appearance_rate,
                "appeared_this_year": appeared_this_year,
            })

    return pd.DataFrame(records)


def evaluate_leave_one_year_out(feat_df, feature_cols):
    """
    For each year Y in the data, train on all rows from years < Y,
    test on rows from year Y. This simulates genuinely predicting
    forward in time, not just interpolating.
    """
    years = sorted(feat_df["year"].unique())
    results = []

    for test_year in years[1:]:  # need at least 1 prior year to train on
        train = feat_df[feat_df["year"] < test_year]
        test = feat_df[feat_df["year"] == test_year]

        if train["appeared_this_year"].nunique() < 2 or len(test) == 0:
            continue  # skip if training data has only one class

        X_train, y_train = train[feature_cols], train["appeared_this_year"]
        X_test, y_test = test[feature_cols], test["appeared_this_year"]

        for model_name, model in [
            ("Logistic Regression", LogisticRegression(max_iter=1000, class_weight="balanced")),
            ("Random Forest", RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")),
        ]:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)

            results.append({
                "test_year": test_year,
                "model": model_name,
                "n_test_topics": len(test),
                "accuracy": accuracy_score(y_test, preds),
                "precision": precision_score(y_test, preds, zero_division=0),
                "recall": recall_score(y_test, preds, zero_division=0),
                "f1": f1_score(y_test, preds, zero_division=0),
            })

    return pd.DataFrame(results)


def main():
    df = load_raw_questions()
    print(f"Loaded {len(df)} raw questions across years: {sorted(df['year'].unique())}")

    feat_df = build_features(df)
    print(f"\nBuilt {len(feat_df)} (topic, year) training examples")
    print(feat_df.head(10).to_string(index=False))

    feature_cols = ["total_appearances", "n_prior_years", "recency_score",
                     "years_since_last", "avg_marks", "avg_difficulty", "appearance_rate"]

    print("\n=== Leave-One-Year-Out Temporal Validation ===")
    results = evaluate_leave_one_year_out(feat_df, feature_cols)
    print(results.to_string(index=False))

    print("\n=== Average performance across test years ===")
    summary = results.groupby("model")[["accuracy", "precision", "recall", "f1"]].mean().round(3)
    print(summary.to_string())

    # Train final model on ALL data for deployment/use in the app
    X_all, y_all = feat_df[feature_cols], feat_df["appeared_this_year"]
    final_model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
    final_model.fit(X_all, y_all)

    with open("topic_predictor_model.pkl", "wb") as f:
        pickle.dump({"model": final_model, "feature_cols": feature_cols}, f)

    results.to_csv("topic_predictor_eval_results.csv", index=False)
    print("\nSaved: topic_predictor_model.pkl, topic_predictor_eval_results.csv")


if __name__ == "__main__":
    main()