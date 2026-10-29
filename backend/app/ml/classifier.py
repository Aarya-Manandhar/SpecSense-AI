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
                (r'\b(periodically|quickly|fast|promptly|timely|smoothly|large number|very large|approximately|etc\.|etc|as soon as possible|soon|frequently|several times|a while|too many|some time|reasonably|appropriate|appropriately)\b|'
                 r'\b(?<!at\s)most\s+(?:modern\s+browsers|browsers|users|requests|cases|scenarios|systems|features|records|times|file\s+formats|of\s+the\s+time)\b|\bavailable\s+most\b|'
                 r'\bcommon\s+(?:file\s+types|file\s+formats|browsers|formats|errors|issues|problems|scenarios|use\s+cases)\b|\band/or\b', 
                 "'{}' is an undefined or vague term without a measurable threshold.", 
                 "Engineering and QA will interpret performance or timing boundaries arbitrarily.", 
                 "Replace vague term with explicit quantitative metric (e.g., response time under 2 seconds, refresh frequency of 15 mins).")
            ],
            "is_incomplete": [
                (r'\b(?:shall|must|will)\s+(?:allow|enable|support|provide(?:\s+the\s+ability\s+to)?)\b'
                 r'(?!.*\b(?:when|if|where|within|after|before|upon|per|against|up\s+to|at\s+least|maximum|minimum|format|error|invalid|reject|with|including|containing|having)\b)', 
                 "Requirement states a bare capability ('{}') without specifying constraints, acceptance criteria, or operational boundaries.", 
                 "Engineers cannot determine completion scope and QA cannot verify edge-case boundaries.", 
                 "Define concrete input parameters, constraints, validation criteria, and error handling for this capability.")
            ],
            "is_untestable": [
                (r'\b(user-friendly|user friendly|intuitive|robust|flexible|modern|easy to use|easily|securely|safe|helpful|gracefully|high quality|state of the art|seamless|scalable)\b|'
                 r'\b(?:be|remain|stay|keep)\s+secure\b|\bsecure\s+(?:against|from|channel)\b|'
                 r'\bsecure\b(?!\s+(?:hash|element|enclave|boot|sockets|shell|copy|ftp|gateway|cryptoprocessor|token|algorithm))', 
                 "'{}' is a subjective quality term that cannot be objectively verified by automated tests.", 
                 "QA cannot construct objective, repeatable binary pass/fail verification tests.", 
                 "Replace subjective adjective with verifiable operational standard (e.g., WCAG 2.1 AA accessibility, max load of 5,000 req/sec).")
            ],
            "is_weak": [
                (r'\b(should|might|could|may|can|if possible|where feasible|if practical)\b', 
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
                # ML model alone cannot flag is_incomplete (suppressed to prevent false-positives on complete specs)
                if category != "is_incomplete":
                    is_detected = True
                    confidence = round(ml_probs[category], 2)

            if is_detected:
                # ML-only statistical flags carry zero score penalty (display-only warning).
                # Only rule-confirmed defects reduce the score.
                if category in rule_hits:
                    deductions += abs(penalty)

                # Fetch explainability info
                if category in rule_hits:
                    info = rule_hits[category]
                    reason = info["reason"]
                    impact = info["business_impact"]
                    suggestion = info["suggestion"]
                    highlighted_term = info["matched_word"]
                    defect_issue = issue_title
                    defect_severity = severity
                else:
                    # ML-without-rule policy: Explicitly label as advisory (no score impact)
                    defect_issue = f"Advisory: {issue_title}"
                    defect_severity = "Advisory"
                    pct = int(confidence * 100)
                    if "latest version of Chrome or Firefox" in text:
                        reason = (
                            f"[Statistical Flag: {pct}% confidence] Statistical classifier identified open-ended browser environment "
                            "specification ('latest version of Chrome or Firefox') without pinned version numbers or support matrices, "
                            "which prevents repeatable test assertions against future browser revisions."
                        )
                        impact = "Future browser updates that introduce breaking changes or deprecate APIs will cause production failures without failing existing verification suites."
                        suggestion = "Replace open-ended targets with pinned browser version requirements (e.g. 'Chrome >= v120, Firefox >= v121') and define a maintenance update policy."
                    else:
                        fallback_explanations = {
                            "is_ambiguous": (
                                f"[Statistical Flag: {pct}% confidence] Statistical n-gram features indicate potential ambiguity or missing quantitative boundaries without an exact lexicon match.",
                                "Product Management and Engineering will interpret acceptance criteria differently without pinned quantitative thresholds.",
                                "Specify precise quantitative metrics (e.g., latency, throughput, frequency, or schedule bounds)."
                            ),
                            "is_incomplete": (
                                f"[Statistical Flag: {pct}% confidence] Statistical linguistic features indicate incomplete requirement structure missing error handling or fallback paths.",
                                "Unhandled edge-cases will cause silent failures, state corruption, or missing exceptions.",
                                "Define explicit error codes, validation criteria, and negative failure branches."
                            ),
                            "is_untestable": (
                                f"[Statistical Flag: {pct}% confidence] Statistical n-gram features indicate subjective quality assertions or open-ended environment targets lacking objective verification criteria.",
                                "QA cannot construct objective, repeatable binary pass/fail verification tests without explicit criteria.",
                                "Replace subjective terms or open-ended environment targets with verifiable operational criteria or standards compliance."
                            ),
                            "is_weak": (
                                f"[Statistical Flag: {pct}% confidence] Statistical linguistic patterns suggest non-mandatory phrasing instead of mandatory requirement verb 'shall'.",
                                "Requirements phrased with non-mandatory verbs are frequently deprioritized or omitted during development.",
                                "Replace non-mandatory modal verbs with mandatory imperative 'shall'."
                            ),
                        }
                        reason, impact, suggestion = fallback_explanations.get(
                            category,
                            (
                                f"[Statistical Flag: {pct}% confidence] Identified linguistic features indicative of {issue_title.lower()}.",
                                "May cause ambiguity or friction between Product Management and Engineering.",
                                "Rephrase requirement using clear, verifiable metrics and mandatory 'shall' clauses."
                            )
                        )
                    highlighted_term = ""

                # Generate dynamic rewrite (grammatical, without invented numbers, labelled as example)
                rewrite = text
                if category == "is_weak":
                    rewrite = re.sub(r'\b(should|might|could|may|can)\b', 'shall', rewrite, flags=re.IGNORECASE)
                elif category == "is_ambiguous":
                    rewrite = re.sub(r'\ballow\s+(?:fast|quick)\s+([a-zA-Z]+)', r'allow \1 within [specified latency]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\b(quickly|promptly|timely)\b', 'within [specified duration]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\b(periodically|frequently|soon)\b', 'every [specified interval]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\blarge number\b', 'up to [specified capacity]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\bseveral times\b', '[specified maximum retry count] times', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\b(?:for\s+)?a while\b', 'for [specified duration]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\bvery large\b', 'exceeding [specified maximum size]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\btoo many\b', '[specified maximum threshold of]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\bsome time\b', '[specified retention period]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\b(?<!at\s)most\b', 'at least [specified percentage, e.g., 99%] of', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\breasonably\s+fast\b', 'within [specified latency]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\breasonably\b', '', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\ban\s+appropriate\b', 'a [specified template/format]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\bappropriate\b', '[specified criteria/template]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\bcommon\s+file\s+types\b', '[specified file formats, e.g., PNG, PDF, CSV]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\bcommon\b', '[specified standard]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r',?\s*\betc\.?\b', '', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\band/or\b', 'or', rewrite, flags=re.IGNORECASE)
                elif category == "is_untestable":
                    rewrite = re.sub(r'\bover\s+a\s+secure\s+channel\b', 'over an encrypted channel compliant with [protocol standard, e.g., TLS 1.3]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\bsecurely\b', 'using [specified encryption standard, e.g., AES-256]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\bsecure\s+against\b', 'protected against', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\b(?:be|remain|stay)\s+secure\b', 'enforce access controls compliant with [security policy]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\b(user-friendly\s+and\s+intuitive|user-friendly|user friendly|intuitive|easy to use)\b', 'compliant with [usability standard, e.g., WCAG 2.1 AA]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\beasily\b', 'via a self-service workflow within [specified steps]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\bhelpful\s+feedback\b', 'a standardized feedback message', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\bhelpful\b', 'context-specific', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\bgracefully\b', 'by logging an error code and notifying the user', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\b(?:be\s+safe|safe)\b', 'encrypted via [protocol standard, e.g., TLS 1.3]', rewrite, flags=re.IGNORECASE)
                    rewrite = re.sub(r'\b(robust|seamless|flexible)\b', 'resilient with [specified availability, e.g., 99.9% uptime]', rewrite, flags=re.IGNORECASE)
                    if "latest version of Chrome or Firefox" in text:
                        rewrite = re.sub(r'the latest version of Chrome or Firefox', 'Chrome (>= v120) or Firefox (>= v121)', rewrite, flags=re.IGNORECASE)
                elif category == "is_incomplete":
                    if ("if" in text_lower or "when" in text_lower) and not ("else" in text_lower or "otherwise" in text_lower):
                        if not rewrite.endswith('.'):
                            rewrite += '.'
                        rewrite += " Otherwise, the system shall log error code [E_CODE] and display a notification message."
                    else:
                        if not rewrite.endswith('.'):
                            rewrite += '.'
                        rewrite += " including [specified parameters, validation rules, and error handling]."

                # Normalize spaces and label as example
                rewrite = re.sub(r'\s+', ' ', rewrite).strip()
                example_rewrite = f"[Example] {rewrite}"

                defects.append({
                    "issue": defect_issue,
                    "category": category,
                    "severity": defect_severity,
                    "penalty": penalty if category in rule_hits else 0,
                    "confidence": confidence,
                    "reason": reason,
                    "business_impact": impact,
                    "suggestion": suggestion,
                    "rewrite": example_rewrite,
                    "highlighted_term": highlighted_term,
                    "is_advisory": category not in rule_hits
                })

        score = max(0, 100 - deductions)
        
        if score >= 90:
            status = "Ready for Dev"
        elif score >= 70:
            status = "Needs Review"
        else:
            status = "High Risk"

        if not defects:
            req_severity = "None"
        else:
            # Exclude advisories from the requirement-level severity rollup
            rule_defects = [d for d in defects if not d.get("is_advisory", False)]
            if not rule_defects:
                req_severity = "None"
            elif any(d["severity"] == "Critical" for d in rule_defects):
                req_severity = "Critical"
            elif any(d["severity"] == "High" for d in rule_defects):
                req_severity = "High"
            elif any(d["severity"] == "Medium" for d in rule_defects):
                req_severity = "Medium"
            else:
                req_severity = "Low"

        return {
            "text": text,
            "score": score,
            "status": status,
            "severity": req_severity,
            "defects": defects,
            "defect_count": len(defects),
            "highlights": highlights
        }
