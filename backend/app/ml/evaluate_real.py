import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[2]
repo_root = Path(__file__).resolve().parents[3]
for directory in (backend_dir, repo_root):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import pandas as pd

try:
    from app.ml.classifier import RequirementClassifier
except ImportError:
    from backend.app.ml.classifier import RequirementClassifier


def main():
    base = Path(__file__).resolve().parents[2] / "data"
    files = [base / "real_promise_nfr_heldout_candidate.csv", base / "eirene_real_annotated.csv"]

    clf = RequirementClassifier()
    if not clf.load_models():
        print("Models not found. Please run `python backend/app/ml/train.py` first to train and save models.")
        sys.exit(1)

    dfs = []
    for f in files:
        if f.exists():
            print(f"Loading {f.name} ({len(pd.read_csv(f))} rows)")
            dfs.append(pd.read_csv(f))
        else:
            print(f"Missing real dataset: {f}")

    if not dfs:
        print("No real datasets available to evaluate.")
        sys.exit(1)

    real_df = pd.concat(dfs, ignore_index=True)
    texts = real_df['requirement_text'].astype(str).tolist()

    counts = {cat: 0 for cat in clf.categories}
    results = []
    for t in texts:
        r = clf.predict_sentence(t)
        results.append(r)
        for d in r['defects']:
            counts[d['category']] += 1

    print(f"Evaluated {len(texts)} requirement sentences on real datasets.")
    print("Defect counts by category:")
    for k, v in counts.items():
        print(f"  {k}: {v}")

    # Save a small summary CSV
    out = Path(__file__).resolve().parents[2] / "data" / "real_evaluation_summary.csv"
    summary_rows = []
    for r in results:
        summary_rows.append({
            'text': r['text'],
            'score': r['score'],
            'status': r['status'],
            'defect_count': r['defect_count']
        })
    pd.DataFrame(summary_rows).to_csv(out, index=False)
    print(f"Saved summary to {out}")


if __name__ == '__main__':
    main()
