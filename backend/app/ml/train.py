import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_recall_fscore_support, roc_auc_score

backend_dir = Path(__file__).resolve().parents[2]
repo_root = Path(__file__).resolve().parents[3]
for directory in (backend_dir, repo_root):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

try:
    from app.ml.classifier import RequirementClassifier
except ImportError:
    from backend.app.ml.classifier import RequirementClassifier


def train_val_test_flow():
    base = Path(__file__).resolve().parents[2] / "data"
    train_path = base / "srs_dataset_train.csv"
    val_path = base / "srs_dataset_val.csv"
    test_path = base / "srs_dataset_test.csv"
    promise_path = base / "real_promise_nfr_heldout_candidate.csv"
    eirene_path = base / "eirene_real_annotated.csv"

    # Verify files exist
    for p in (train_path, val_path, test_path):
        if not p.exists():
            print(f"Required dataset missing: {p}")
            return

    print("Loading datasets...")
    df_train = pd.read_csv(train_path)
    df_val = pd.read_csv(val_path)
    df_test = pd.read_csv(test_path)

    print(f"Train rows={len(df_train)}, val rows={len(df_val)}, test rows={len(df_test)}")

    clf = RequirementClassifier()

    # 1) Fit model on train only
    print("Training models on train set...")
    clf.train(df_train)

    # 2) Pick thresholds using validation set
    print("Tuning thresholds on validation set...")
    X_val = df_val["requirement_text"].astype(str)
    X_val_vec = clf.vectorizer.transform(X_val)
    categories = clf.categories

    for category in categories:
        if category not in clf.models:
            print(f"Warning: no model for {category}")
            continue
        y_val = df_val[category].astype(int)
        probs = clf.models[category].predict_proba(X_val_vec)[:, 1]

        best_threshold = 0.5
        best_f1 = -1.0

        if len(np.unique(y_val)) < 2:
            print(f"Validation labels for {category} contain only one class; using default threshold {best_threshold}")
            clf.thresholds[category] = best_threshold
            continue

        for threshold in np.linspace(0.1, 0.9, 41):
            preds = (probs >= threshold).astype(int)
            f1 = f1_score(y_val, preds, zero_division=0)
            if f1 > best_f1:
                best_f1 = f1
                best_threshold = threshold

        clf.thresholds[category] = float(best_threshold)
        prec, rec, f1, _ = precision_recall_fscore_support(y_val, (probs >= best_threshold).astype(int), average='binary', zero_division=0)
        try:
            roc = roc_auc_score(y_val, probs)
        except Exception:
            roc = float('nan')
        print(f"{category}: best_threshold={best_threshold:.2f}, f1={f1:.3f}, prec={prec:.3f}, rec={rec:.3f}, auc={roc}")

    # Persist models and thresholds
    clf.save_models()
    print("Saved trained models and thresholds to model directory.")

    # 3) Report metrics on test set (no retraining)
    print("Evaluating on test set...")
    X_test = df_test["requirement_text"].astype(str)
    X_test_vec = clf.vectorizer.transform(X_test)

    for category in categories:
        y_test = df_test[category].astype(int)
        if category not in clf.models:
            continue
        probs = clf.models[category].predict_proba(X_test_vec)[:, 1]
        thresh = clf.thresholds.get(category, 0.5)
        preds = (probs >= thresh).astype(int)
        prec, rec, f1, _ = precision_recall_fscore_support(y_test, preds, average='binary', zero_division=0)
        try:
            auc = roc_auc_score(y_test, probs)
        except Exception:
            auc = float('nan')
        print(f"TEST {category}: threshold={thresh:.2f}, precision={prec:.3f}, recall={rec:.3f}, f1={f1:.3f}, auc={auc}")

    # 4) Run trained model (no retraining) on real datasets: promise + eirene
    real_dfs = []
    for p in (promise_path, eirene_path):
        if Path(p).exists():
            real_dfs.append(pd.read_csv(p))
        else:
            print(f"Real dataset missing (skipping): {p}")

    if real_dfs:
        real_df = pd.concat(real_dfs, ignore_index=True)
        print(f"Running model on real data (rows={len(real_df)})...")
        sample_texts = real_df["requirement_text"].astype(str)
        results = [clf.predict_sentence(t) for t in sample_texts]
        # Summarize defect counts per category
        counts = {cat: 0 for cat in categories}
        for r in results:
            for d in r["defects"]:
                counts[d["category"]] += 1
        print("Real-data defect counts (by category):")
        for cat, cnt in counts.items():
            print(f"  {cat}: {cnt}")


if __name__ == "__main__":
    train_val_test_flow()
