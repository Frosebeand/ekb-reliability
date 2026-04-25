from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from ekb_reliability.ml.dataset_builder import augment_bom_style_text, load_curated_text_dataset


def _top_features(pipe: Pipeline, top_n: int = 15) -> dict[str, list[dict[str, float]]]:
    vec = pipe.named_steps["tfidf"]
    clf = pipe.named_steps["clf"]
    feature_names = vec.get_feature_names_out()
    classes = list(clf.classes_)
    out: dict[str, list[dict[str, float]]] = {}
    coef = getattr(clf, "coef_", None)
    if coef is None:
        return out
    for idx, cls in enumerate(classes):
        weights = coef[idx]
        top_idx = weights.argsort()[-top_n:][::-1]
        out[cls] = [{"feature": str(feature_names[i]), "weight": float(weights[i])} for i in top_idx]
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-zip", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--metrics-output")
    args = parser.parse_args()

    df = load_curated_text_dataset(args.dataset_zip)
    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["label"],
    )

    train_rows = []
    for _, row in train_df.iterrows():
        for variant in augment_bom_style_text(row["text"]):
            train_rows.append({"text": variant, "label": row["label"]})
    train_aug_df = pd.concat([train_df[["text", "label"]].copy(), pd.DataFrame(train_rows)], ignore_index=True).drop_duplicates()
    test_eval_df = test_df[["text", "label"]].copy().drop_duplicates()

    X_train, y_train = train_aug_df["text"], train_aug_df["label"]
    X_test, y_test = test_eval_df["text"], test_eval_df["label"]

    pipe = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20000)),
            ("clf", SGDClassifier(loss="log_loss", max_iter=2000, random_state=42)),
        ]
    )
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_test)

    metrics = {
        "accuracy": accuracy_score(y_test, preds),
        "classification_report": classification_report(y_test, preds, output_dict=True),
        "confusion_matrix": confusion_matrix(y_test, preds, labels=list(pipe.classes_)).tolist(),
        "labels": list(pipe.classes_),
        "top_features": _top_features(pipe),
        "n_test": int(len(y_test)),
    }
    print("accuracy:", metrics["accuracy"])
    print(classification_report(y_test, preds))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, output)

    if args.metrics_output:
        metrics_path = Path(args.metrics_output)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
