import os
import pandas as pd

def generate_srs_dataset() -> pd.DataFrame:
    """
    Generates a rich, structured dataset of software requirements labeled for 
    Ambiguity, Incompleteness, Non-Testability, and Weak Phrasing.
    """
    data = []

    # 1. Good / Pass Requirements (High Quality)
    good_requirements = [
        ("The system shall process user authentication requests within 200 milliseconds under a load of 500 requests per second.", "Pass", "Clear performance benchmark with explicit latency and load metrics.", "None", "The system shall process user authentication requests within 200 milliseconds under a load of 500 requests per second."),
        ("The system shall encrypt all stored user passwords using AES-256 encryption algorithm.", "Pass", "Definitive security algorithm specified without ambiguity.", "None", "The system shall encrypt all stored user passwords using AES-256 encryption algorithm."),
        ("If the email address is already registered, the system shall display an error message reading 'Email already in use' and return the user to the registration form.", "Pass", "Fully specifies input, condition, exact error message, and recovery action.", "None", "If the email address is already registered, the system shall display an error message reading 'Email already in use' and return the user to the registration form."),
        ("The system shall generate a monthly sales summary report in PDF format on the 1st day of every calendar month at 00:00 UTC.", "Pass", "Explicit schedule, format, and trigger timing.", "None", "The system shall generate a monthly sales summary report in PDF format on the 1st day of every calendar month at 00:00 UTC."),
        ("The application shall maintain 99.9% uptime over any given 30-day rolling window.", "Pass", "Measurable reliability SLA percentage and timeframe.", "None", "The application shall maintain 99.9% uptime over any given 30-day rolling window."),
        ("The system shall export customer records to a CSV file containing ID, Name, Email, and CreatedAt columns.", "Pass", "Explicit file format and precise column definitions.", "None", "The system shall export customer records to a CSV file containing ID, Name, Email, and CreatedAt columns."),
        ("If the database connection fails, the system shall log the error to AWS CloudWatch and retry connection every 5 seconds for up to 3 attempts.", "Pass", "Handles failure scenario, logging target, and retry limit explicitly.", "None", "If the database connection fails, the system shall log the error to AWS CloudWatch and retry connection every 5 seconds for up to 3 attempts.")
    ]

    for text, status, reason, impact, rewrite in good_requirements:
        data.append({
            "requirement_text": text,
            "is_ambiguous": 0,
            "is_incomplete": 0,
            "is_untestable": 0,
            "is_weak": 0,
            "reason": reason,
            "business_impact": impact,
            "rewrite": rewrite
        })

    # Add more good requirements for dataset diversity
    additional_good_requirements = [
        ("The system shall archive completed orders older than 90 days to cold storage.", "Pass", "Explicit retention and archival behavior.", "None", "The system shall archive completed orders older than 90 days to cold storage."),
        ("When the inventory level falls below 10 units, the system shall generate a reorder alert email to the procurement team.", "Pass", "Defines trigger, recipient, and action clearly.", "None", "When the inventory level falls below 10 units, the system shall generate a reorder alert email to the procurement team."),
        ("The system shall validate all user input fields against type, range, and required value constraints before saving.", "Pass", "Specifies validation behavior and save conditions.", "None", "The system shall validate all user input fields against type, range, and required value constraints before saving."),
        ("The application shall allow a logged-in user to reset their password using a secure email token valid for 15 minutes.", "Pass", "Includes authentication state, security token, and expiration time.", "None", "The application shall allow a logged-in user to reset their password using a secure email token valid for 15 minutes."),
        ("The system shall produce an audit log entry for every administrative action including user ID, timestamp, and action type.", "Pass", "Precise logging requirements are defined clearly.", "None", "The system shall produce an audit log entry for every administrative action including user ID, timestamp, and action type.")
    ]
    for text, status, reason, impact, rewrite in additional_good_requirements:
        data.append({
            "requirement_text": text,
            "is_ambiguous": 0,
            "is_incomplete": 0,
            "is_untestable": 0,
            "is_weak": 0,
            "reason": reason,
            "business_impact": impact,
            "rewrite": rewrite
        })

    # 2. Ambiguous Requirements
    ambiguous_requirements = [
        ("The system shall update customer records periodically.", 1, 0, 0, 0, "'Periodically' is an undefined time frequency.", "Developers may implement a 24-hour batch job while business stakeholders expected 1-minute real-time updates.", "The system shall update customer records every 15 minutes."),
        ("The backend should respond quickly to search queries.", 1, 0, 0, 1, "'Quickly' is subjective and lacks a measurable millisecond or second threshold.", "Performance cannot be SLA tested; client may reject response times.", "The system shall respond to search queries within 300 milliseconds."),
        ("The application shall support a large number of concurrent users.", 1, 0, 0, 0, "'Large number' is vague and non-quantifiable.", "Infrastructure will fail to scale if server capacity is under-provisioned.", "The system shall support up to 10,000 concurrent active users."),
        ("The system shall backup database contents approximately once a day.", 1, 0, 0, 0, "'Approximately' introduces uncertainty in schedule.", "Data loss window is unpredictable during outages.", "The system shall backup database contents daily at 02:00 UTC."),
        ("The interface shall display user details, sales history, etc.", 1, 0, 0, 0, "'Etc.' leaves the required field list undefined.", "Engineers will omit critical compliance fields.", "The interface shall display user details, sales history, account status, and registration date."),
        ("The system shall produce reports quickly when requested.", 1, 0, 0, 0, "'Quickly' does not define an exact response time.", "Teams cannot agree on acceptable report latency.", "The system shall produce reports within 10 seconds when requested."),
        ("The application shall support several file formats.", 1, 0, 0, 0, "'Several' is vague and leaves the supported formats undefined.", "Developers may implement only one file type by default.", "The application shall support CSV, PDF, and JSON import formats."),
        ("The interface should display customer information comprehensively.", 1, 0, 0, 1, "'Comprehensively' is subjective and not measurable.", "Important fields may be omitted in the UI.", "The interface shall display customer name, email, phone, and order history.")
    ]

    for text, amb, inc, unt, weak, reason, impact, rewrite in ambiguous_requirements:
        data.append({
            "requirement_text": text,
            "is_ambiguous": amb,
            "is_incomplete": inc,
            "is_untestable": unt,
            "is_weak": weak,
            "reason": reason,
            "business_impact": impact,
            "rewrite": rewrite
        })

    # 3. Incomplete Requirements
    incomplete_requirements = [
        ("If the user submits a valid promo code, apply a 10% discount to the cart total.", 0, 1, 0, 0, "Missing the failure branch (what happens if the promo code is invalid or expired?).", "Users who enter invalid codes see broken state or unhandled exceptions.", "If the user submits a valid promo code, apply a 10% discount; if invalid, display 'Invalid Promo Code' and preserve the current total."),
        ("When a payment is processed, send an invoice.", 0, 1, 0, 0, "Does not specify who receives the invoice, via what channel (email/SMS), or what happens if payment fails.", "Invoices may fail to send to the correct customer email.", "When a payment succeeds, send a PDF invoice to the account holder's registered email within 60 seconds."),
        ("The system shall import data from the CSV file.", 0, 1, 0, 0, "Missing file schema, validation rules, and error handling for malformed rows.", "Import script will crash when parsing invalid CSV columns.", "The system shall import customer data from a UTF-8 encoded CSV file, validating required columns (Name, Email)."),
        ("The admin can delete user accounts.", 0, 1, 0, 0, "Missing confirmation step, cascade deletion scope, or soft-delete policy.", "Accidental deletions will destroy related transactional history permanently.", "The system shall allow admins to soft-delete user accounts after displaying a confirmation prompt."),
        ("If the payment fails, notify the customer.", 0, 1, 0, 0, "Lacks the recovery or retry behavior for failed payments.", "Customers will not know whether their order completed or needs action.", "If the payment fails, display an error message and allow the customer to retry or choose another payment method."),
        ("The system shall import XML files.", 0, 1, 0, 0, "Missing schema, validation rules, and error handling for invalid XML.", "Parsing errors will break the import pipeline.", "The system shall import XML files with a validated schema and report malformed elements to the user."),
        ("When a ticket is closed, update the report.", 0, 1, 0, 0, "Does not specify which report is updated or what fields change.", "Reports may still show stale ticket status.", "When a ticket is closed, update the monthly incident report with closure date and resolution summary."),
        ("The system shall retain user sessions.", 0, 1, 0, 0, "Missing time limit and invalidation rules for sessions.", "Sessions may stay active indefinitely and create security risk.", "The system shall retain user sessions for 30 minutes of inactivity and prompt re-authentication thereafter.")
    ]

    for text, amb, inc, unt, weak, reason, impact, rewrite in incomplete_requirements:
        data.append({
            "requirement_text": text,
            "is_ambiguous": amb,
            "is_incomplete": inc,
            "is_untestable": unt,
            "is_weak": weak,
            "reason": reason,
            "business_impact": impact,
            "rewrite": rewrite
        })

    # 4. Non-Testable Requirements
    untestable_requirements = [
        ("The user interface must be modern, highly intuitive, and user-friendly.", 0, 0, 1, 0, "Subjective qualities ('intuitive', 'user-friendly') cannot be programmatically verified by QA.", "QA team cannot write pass/fail automated test cases.", "The user interface shall enable users to complete order checkout within 3 clicks from the product page."),
        ("The application should be fast and responsive on mobile devices.", 0, 0, 1, 1, "Vague adverbs ('fast', 'responsive') without defined FPS or load latency metrics.", "Performance testing cannot establish a benchmark.", "The application shall render screens within 100 milliseconds on iOS and Android devices."),
        ("The system shall be extremely robust against network disruptions.", 0, 0, 1, 0, "'Extremely robust' is a subjective descriptor.", "No objective pass/fail criteria for chaos/resilience testing.", "The system shall automatically reconnect within 3 seconds of network failure without data loss."),
        ("The system must maintain high security standards.", 0, 0, 1, 0, "'High security standards' is undefined.", "Security audit will fail due to lack of compliance specs.", "The system shall enforce OWASP Top 10 compliance and require multi-factor authentication for all admin logins."),
        ("The application shall feel seamless and delightful to use.", 0, 0, 1, 0, "'Seamless' and 'delightful' are subjective UX terms.", "No objective criteria exist to validate the experience.", "The application shall complete account setup within 2 minutes with a visible progress indicator."),
        ("The platform must be extremely scalable.", 0, 0, 1, 0, "'Extremely scalable' is not measurable.", "Architects cannot define capacity requirements accurately.", "The platform shall support a 10x increase in concurrent users without degradation."),
        ("The user experience should be exceptional.", 0, 0, 1, 1, "'Exceptional' is subjective and cannot be tested objectively.", "QA cannot determine acceptance consistently.", "The user experience shall allow users to complete a purchase in under five screens."),
        ("The system must provide industry-leading security.", 0, 0, 1, 0, "'Industry-leading' is vague and lacks compliance criteria.", "Security reviews cannot verify the requirement.", "The system shall require password complexity, MFA for admins, and quarterly security scanning.")
    ]

    for text, amb, inc, unt, weak, reason, impact, rewrite in untestable_requirements:
        data.append({
            "requirement_text": text,
            "is_ambiguous": amb,
            "is_incomplete": inc,
            "is_untestable": unt,
            "is_weak": weak,
            "reason": reason,
            "business_impact": impact,
            "rewrite": rewrite
        })

    # 5. Weak Requirements (Escape Clause Phrasing)
    weak_requirements = [
        ("The system should backup files if possible.", 0, 0, 0, 1, "Uses modal verb 'should' and escape clause 'if possible' instead of mandatory 'shall'.", "Development team can treat backups as optional, risking compliance failure.", "The system shall backup configuration files daily at midnight."),
        ("The mobile app might notify users about new updates.", 0, 0, 0, 1, "Uses speculative 'might' which makes the requirement optional.", "Push notification feature will be omitted or inconsistently built.", "The mobile app shall send push notifications for critical software updates."),
        ("Developers could implement data caching where feasible.", 0, 0, 0, 1, "Uses 'could' and 'where feasible' which lacks binding commitment.", "Caching will be skipped, leading to poor production performance under high load.", "The system shall cache frequently queried API responses in Redis with a 5-minute TTL."),
        ("The software may support multi-language localizations.", 0, 0, 0, 1, "Uses permissive 'may' instead of definitive obligation.", "Localization effort won't be prioritized in sprint execution.", "The software shall support English and Spanish language localizations."),
        ("The system may optionally cache profile pictures.", 0, 0, 0, 1, "'May optionally' creates a non-mandatory requirement.", "Caching will be skipped if implementers decide it is unnecessary.", "The system shall cache profile pictures for 30 minutes to reduce load times."),
        ("The payment gateway could support additional currencies.", 0, 0, 0, 1, "'Could support' avoids committing to the feature.", "International payments may never be implemented.", "The payment gateway shall support USD, EUR, and GBP transactions."),
        ("The app might send a notification if activity is detected.", 0, 0, 0, 1, "'Might' makes the notification optional and uncertain.", "Users may not receive critical alerts consistently.", "The app shall send a notification immediately when suspicious activity is detected."),
        ("Developers should consider adding offline support.", 0, 0, 0, 1, "'Should consider' is not a binding requirement.", "Offline support may be deferred indefinitely.", "The system shall support offline mode for viewing previously loaded data." )
    ]

    for text, amb, inc, unt, weak, reason, impact, rewrite in weak_requirements:
        data.append({
            "requirement_text": text,
            "is_ambiguous": amb,
            "is_incomplete": inc,
            "is_untestable": unt,
            "is_weak": weak,
            "reason": reason,
            "business_impact": impact,
            "rewrite": rewrite
        })

    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, "requirements_dataset.csv")
    
    df = generate_srs_dataset()
    df.to_csv(csv_path, index=False)
    print(f"Dataset generated successfully with {len(df)} samples at: {csv_path}")
