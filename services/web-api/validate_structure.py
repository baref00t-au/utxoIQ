"""Validate the Web API service structure."""
import os
import sys

def check_file_exists(filepath):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✓ {filepath}")
        return True
    else:
        print(f"✗ {filepath} - MISSING")
        return False

def main():
    """Validate service structure."""
    print("Validating Web API Service Structure\n")
    
    required_files = [
        "src/main.py",
        "src/config.py",
        "src/models/__init__.py",
        "src/models/insights.py",
        "src/models/errors.py",
        "src/models/auth.py",
        "src/models/alerts.py",
        "src/models/feedback.py",
        "src/models/daily_brief.py",
        "src/models/chat.py",
        "src/models/billing.py",
        "src/models/email_preferences.py",
        "src/websocket/__init__.py",
        "src/websocket/manager.py",
        "src/middleware/__init__.py",
        "src/middleware/auth.py",
        "src/middleware/rate_limit.py",
        "src/middleware/response_headers.py",
        "src/routes/__init__.py",
        "src/routes/websocket.py",
        "src/routes/insights.py",
        "src/routes/alerts.py",
        "src/routes/feedback.py",
        "src/routes/daily_brief.py",
        "src/routes/chat.py",
        "src/routes/billing.py",
        "src/routes/email_preferences.py",
        "src/routes/white_label.py",
        "src/services/__init__.py",
        "src/services/insights_service.py",
        "src/services/alerts_service.py",
        "src/services/feedback_service.py",
        "src/services/daily_brief_service.py",
        "src/services/billing_service.py",
        "src/services/email_preferences_service.py",
        "src/services/white_label_service.py",
        "src/services/cost_tracking_service.py",
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/test_api.py",
        "tests/test_websocket.py",
        "tests/test_rate_limiting.py",
        "tests/test_guest_mode.py",
        "tests/test_openapi_schema.py",
        "requirements.txt",
        "Dockerfile",
        "pytest.ini",
        "README.md",
        ".env.example"
    ]
    
    all_exist = True
    for filepath in required_files:
        if not check_file_exists(filepath):
            all_exist = False
    
    print(f"\n{'='*50}")
    if all_exist:
        print("✓ All required files present!")
        print("✓ Web API service structure is valid")
        return 0
    else:
        print("✗ Some files are missing")
        return 1

if __name__ == "__main__":
    sys.exit(main())
