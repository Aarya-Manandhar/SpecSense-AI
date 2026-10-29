"""
Run the SpecSense auditor on the synthetic CTS held-out SRS and print per-line results.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.app.ml.preprocessor import RequirementPreprocessor
from backend.app.ml.classifier import RequirementClassifier

SRS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'test_data', 'synthetic_cts_srs.txt')

def main():
    with open(SRS_PATH, encoding='utf-8') as f:
        raw = f.read()

    preprocessor = RequirementPreprocessor()
    reqs = preprocessor.extract_sentences(raw)

    classifier = RequirementClassifier()
    classifier.load_models()

    print(f"\n{'='*72}")
    print("SYNTHETIC CHEMICAL TRACKING SYSTEM (CTS) — Held-Out SRS Audit")
    print(f"{'='*72}")
    print(f"Requirements extracted: {len(reqs)}")
    print(f"Lines excluded:         {len(preprocessor.exclusion_log)}")
    print()

    total_score = 0
    for i, req in enumerate(reqs, 1):
        result = classifier.predict_sentence(req)
        score = result['score']
        total_score += score
        defects = result['defects']
        sev = result['severity']

        # Print requirement header
        flag = "OK" if not defects else "!!"
        print(f"  [{flag}] REQ-{i:03d}  Score:{score:3d}/100  Severity:{sev:<8s}  Defects:{len(defects)}")
        print(f"       \"{req}\"")

        for d in defects:
            cat_short = {
                'is_ambiguous':   'AMBIGUOUS ',
                'is_incomplete':  'INCOMPLETE',
                'is_untestable':  'UNTESTABLE',
                'is_weak':        'WEAK      ',
            }.get(d['category'], d['category'])
            issue = d['issue']
            rule_or_ml = "rule" if d['confidence'] == 0.95 else f"ML {int(d['confidence']*100)}%"
            print(f"         [{cat_short}] ({rule_or_ml}) penalty:{d['penalty']:+d}  — {d['reason'][:80]}")
        print()

    health = round(total_score / len(reqs)) if reqs else 0
    print(f"{'='*72}")
    print(f"  Health Index: {health}/100")
    print(f"{'='*72}\n")

    print("Excluded lines:")
    for e in preprocessor.exclusion_log:
        print(f"  [{e['reason']}]  {e['line'][:90]}")

if __name__ == '__main__':
    main()
