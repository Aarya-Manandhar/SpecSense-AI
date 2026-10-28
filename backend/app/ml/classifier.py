import os
import re
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import f1_score, precision_recall_fscore_support, roc_auc_score

class RequirementClassifier:
    """
    Requirement Quality & Defect Intelligence Classifier.
    Combines TF-IDF + Logistic Regression with rule-based explainability patterns.
    """
    def __init__(self, model_dir: str | None = None):
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), "models")
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        self.vectorizer = TfidfVectorizer(

            ngram_range=(1, 3),
            min_df=1,
            max_df=0.85,
            stop_words='english',
            lowercase=True
        )
        self.categories = ["is_ambiguous", "is_incomplete", "is_untestable", "is_weak"]
        self.models = {}
        self.thresholds = {category: 0.6 for category in self.categories}
        self.is_trained = False

        # Rule-based heuristics for high-explainability fallback
        self.rules = {
            "is_ambiguous": [
                (r'\b(periodically|quickly|fast|promptly|timely|smoothly|large number|approximately|etc\.|as soon as possible|soon|frequently)\b', 
                 "'{}' is an undefined or vague term without a measurable threshold.", 
                 "Engineering and QA will interpret performance or timing boundaries arbitrarily.", 
                 "Replace vague term with explicit quantitative metric (e.g., response time under 2 seconds, refresh frequency of 15 mins).")
            ],
            "is_incomplete": [
                (r'\b(if|when)\b(?!.*(?:else|otherwise|if invalid|display error|return error|log error|raise error|reject))', 
                 "Conditional requirement specifies trigger condition but lacks handling for invalid input or failure scenarios.", 
                 "Unhandled edge cases will cause unexpected state errors, silent failures, or unhandled exceptions.", 
                 "Specify explicit exception handling, fallback logic, or error message display.")
            ],
            "is_untestable": [
                (r'\b(user-friendly|user friendly|intuitive|robust|flexible|modern|easy to use|high quality|state of the art|seamless|scalable)\b', 
                 "'{}' is a subjective quality term that cannot be objectively verified by automated tests.", 
                 "QA cannot construct objective, repeatable binary pass/fail verification tests.", 
                 "Replace subjective adjective with verifiable operational standard (e.g., WCAG 2.1 AA accessibility, max load of 5,000 req/sec).")
            ],
            "is_weak": [
                (r'\b(should|might|could|may|if possible|where feasible|if practical)\b', 
                 "Uses non-mandatory verb or escape clause '{}' instead of imperative requirement verb 'shall'.", 
                 "Requirements phrased with non-mandatory verbs are frequently deprioritized or omitted during development.", 
                 "Replace weak modal verb with mandatory imperative 'shall'.")
            ]
        }

    def train(self, df: pd.DataFrame):
        """
        Trains TF-IDF vectorizer and Logistic Regression models for each defect class.
        """
        X_raw = df["requirement_text"]
        X_vec = self.vectorizer.fit_transform(X_raw)

        for category in self.categories:
            y = df[category]
            clf = LogisticRegression(C=1.0, max_iter=200, class_weight='balanced')
            clf.fit(X_vec, y)
            self.models[category] = clf

        self.is_trained = True
        self.save_models()

    def train_with_validation(self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
        """
        Trains with a validation split, chooses the best threshold per label, and outputs metrics.
        """
        X_raw = df["requirement_text"].astype(str)
        y = df[self.categories]

        X_train, X_val, y_train, y_val = train_test_split(
            X_raw,
            y,
            test_size=test_size,
            random_state=random_state,
            shuffle=True
        )

        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_val_vec = self.vectorizer.transform(X_val)

        print(f"Training on {X_train_vec.shape[0]} samples, validating on {X_val_vec.shape[0]} samples.")

        for category in self.categories:
            y_train_cat = y_train[category].astype(int)
            y_val_cat = y_val[category].astype(int)
            positive_count = int(y_train_cat.sum())
            negative_count = int(len(y_train_cat) - positive_count)

            if positive_count < 2 or negative_count < 2:
                print(
                    f"Using simple LogisticRegression for '{category}' due to insufficient class balance "
                    f"(pos={positive_count}, neg={negative_count})."
                )
                clf = LogisticRegression(
                    C=1.0,
                    max_iter=500,
                    class_weight='balanced',
                    solver='liblinear'
                )
                clf.fit(X_train_vec, y_train_cat)
            else:
                n_splits = min(5, positive_count, negative_count)
                cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
                clf = LogisticRegressionCV(
                    Cs=[0.01, 0.1, 1.0, 10.0],
                    cv=cv,
                    penalty='l2',
                    solver='liblinear',
                    l1_ratios=(0,),
                    class_weight='balanced',
                    max_iter=500,
                    scoring='f1',
                    n_jobs=-1
                )
                clf.fit(X_train_vec, y_train_cat)

            self.models[category] = clf

            y_val_probs = clf.predict_proba(X_val_vec)[:, 1]
            best_threshold = 0.5
            best_f1 = 0.0
            roc_auc = 'n/a'

            if len(np.unique(y_val_cat)) < 2:
                print(f"Skipping threshold tuning for '{category}' because validation labels contain only one class.")
                self.thresholds[category] = best_threshold
            else:
                for threshold in np.linspace(0.1, 0.9, 41):
                    y_pred_val = (y_val_probs >= threshold).astype(int)
                    f1 = f1_score(y_val_cat, y_pred_val, zero_division=0)
                    if f1 > best_f1:
                        best_f1 = f1
                        best_threshold = threshold

                self.thresholds[category] = best_threshold

                precision, recall, f1, _ = precision_recall_fscore_support(
                    y_val_cat,
                    (y_val_probs >= best_threshold).astype(int),
                    average='binary',
                    zero_division=0
                )
                if len(np.unique(y_val_cat)) > 1:
                    roc_auc = roc_auc_score(y_val_cat, y_val_probs)

                print(
                    f"Category={category}, best_threshold={best_threshold:.2f}, "
                    f"f1={best_f1:.3f}, precision={precision:.3f}, recall={recall:.3f}, roc_auc={roc_auc}"
                )

        self.is_trained = True
        self.save_models()

    def save_models(self):
        """
        Persists vectorizer and trained classifiers to disk using joblib.
        """
        joblib.dump(self.vectorizer, os.path.join(self.model_dir, "vectorizer.joblib"))
        joblib.dump(self.thresholds, os.path.join(self.model_dir, "thresholds.joblib"))
        for category, clf in self.models.items():
            joblib.dump(clf, os.path.join(self.model_dir, f"{category}_model.joblib"))

    def load_models(self) -> bool:
        """
        Loads trained vectorizer and classifier models from disk if present.
        """
        vec_path = os.path.join(self.model_dir, "vectorizer.joblib")
        if not os.path.exists(vec_path):
            return False

        try:
            self.vectorizer = joblib.load(vec_path)
            threshold_path = os.path.join(self.model_dir, "thresholds.joblib")
            if os.path.exists(threshold_path):
                self.thresholds = joblib.load(threshold_path)

            for category in self.categories:
                model_path = os.path.join(self.model_dir, f"{category}_model.joblib")
                if os.path.exists(model_path):
                    self.models[category] = joblib.load(model_path)
            self.is_trained = True
            return True
        except Exception:
            return False

    def predict_sentence(self, text: str) -> dict:
        """
        Analyzes a single requirement sentence and returns detected defects, confidence, 
        explanations, business impact, highlights, and rewrites.
        """
        if not text:
            text = ""
        text = text.encode('utf-8', 'ignore').decode('utf-8', 'ignore')

        defects = []
        deductions = 0
        highlights = []

        # Run rule-based heuristic checks for explainable features
        text_lower = text.lower()

        
        rule_hits = {}
        for category, rule_list in self.rules.items():
            for pattern, reason_template, impact, suggestion in rule_list:
                match = re.search(pattern, text_lower)
                if match:
                    matched_word = match.group(0)
                    rule_hits[category] = {
                        "matched_word": matched_word,
                        "reason": reason_template.format(matched_word),
                        "business_impact": impact,
                        "suggestion": suggestion
                    }
                    if matched_word not in highlights:
                        highlights.append(matched_word)

        # Run ML model prediction if trained
        ml_probs = {}
        if self.is_trained:
            X_vec = self.vectorizer.transform([text])
            for category in self.categories:
                if category in self.models:
                    prob = self.models[category].predict_proba(X_vec)[0][1]
                    ml_probs[category] = float(prob)
        
        # Category penalty weights & severity
        category_weights = {
            "is_ambiguous": ("Ambiguous Requirement", -30, "High"),
            "is_incomplete": ("Incomplete Requirement", -40, "Critical"),
            "is_untestable": ("Non-Testable Requirement", -20, "Medium"),
            "is_weak": ("Weak Phrasing", -10, "Low")
        }

        for category, (issue_title, penalty, severity) in category_weights.items():
            is_detected = False
            confidence = 0.5
            threshold = self.thresholds.get(category, 0.6)

            if category in rule_hits:
                is_detected = True
                confidence = 0.95
            elif category in ml_probs and ml_probs[category] >= threshold:
                is_detected = True
                confidence = round(ml_probs[category], 2)

            if is_detected:
                deductions += abs(penalty)
                
                # Fetch explainability info
                if category in rule_hits:
                    info = rule_hits[category]
                    reason = info["reason"]
                    impact = info["business_impact"]
                    suggestion = info["suggestion"]
                    highlighted_term = info["matched_word"]
                else:
                    reason = f"Identified linguistic features indicative of {issue_title.lower()}."
                    impact = "May cause ambiguity or friction between Product Management and Engineering."
                    suggestion = "Rephrase requirement using clear, verifiable metrics and mandatory 'shall' clauses."
                    highlighted_term = ""

                # Generate dynamic rewrite
                rewrite = text
                if category == "is_weak":
                    rewrite = re.sub(r'\b(should|might|could|may)\b', 'shall', rewrite, flags=re.IGNORECASE)
                if category == "is_ambiguous":
                    rewrite = re.sub(r'\b(quickly|fast|promptly|timely)\b', 'within 2 seconds', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\b(periodically|frequently|soon)\b', 'every 15 minutes', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\blarge number\b', 'up to 10,000 concurrent users', rewrite, flags=re.IGNORECASE)
                if category == "is_untestable":
                    rewrite = re.sub(r'\b(user-friendly|user friendly|intuitive|easy to use)\b', 'compliant with WCAG 2.1 AA standards', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\b(robust|seamless|flexible)\b', 'resilient with 99.99% uptime', rewrite, flags=re.IGNORECASE)
                if category == "is_incomplete" and ("if" in text_lower or "when" in text_lower) and not ("else" in text_lower or "otherwise" in text_lower):
                    if not rewrite.endswith('.'):
                        rewrite += '.'
                    rewrite += " Otherwise, the system shall log an error and display an appropriate error notification."

                defects.append({
                    "issue": issue_title,
                    "category": category,
                    "severity": severity,
                    "penalty": penalty,
                    "confidence": confidence,
                    "reason": reason,
                    "business_impact": impact,
                    "suggestion": suggestion,
                    "rewrite": rewrite,
                    "highlighted_term": highlighted_term
                })

        score = max(0, 100 - deductions)
        
        if score >= 90:
            status = "Ready for Dev"
        elif score >= 70:
            status = "Needs Review"
        else:
            status = "High Risk"

        return {
            "text": text,
            "score": score,
            "status": status,
            "defects": defects,
            "defect_count": len(defects),
            "highlights": highlights
        }
