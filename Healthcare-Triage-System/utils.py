import yaml
from typing import List, Dict, Any
from datetime import datetime
import pytz
from constants import ModelType, ErrorMessages


def load_settings() -> Dict[str, Any]:
    """Load application settings from YAML"""
    with open('settings.yaml', 'r') as f:
        return yaml.safe_load(f)


def get_formatted_datetime(timezone_str: str) -> str:
    """Get formatted datetime string for given timezone"""
    tz = pytz.timezone(timezone_str)
    return datetime.now(tz).strftime('%Y-%m-%d %H:%M %Z')


def get_latest_messages(messages: List[dict], num_messages: int = 3) -> str:
    """Gets the latest n messages from the conversation history"""
    return "\n\n".join([message.content for message in messages[-num_messages:]])


def analyze_symptoms_severity(symptoms: List[str], severity: str) -> bool:
    """
    Analyze symptoms and severity to determine if urgent care is needed
    Returns: True if urgent care is needed, False otherwise
    """
    urgent_symptoms = ["chest pain", "difficulty breathing", "severe pain"]
    return (
            severity.lower() == "severe" or
            any(urgent in [s.lower() for s in symptoms] for urgent in urgent_symptoms)
    )


def validate_appointment_request(appointment_type: str, preferred_date: str) -> None:
    """Validate appointment request parameters"""
    try:
        datetime.strptime(preferred_date, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD")

    valid_types = ["virtual", "in-person", "specialist"]
    if appointment_type not in valid_types:
        raise ValueError(f"Invalid appointment type. Must be one of: {', '.join(valid_types)}")


def format_error_response(error: Exception, context: str = "general") -> str:
    """Format error response based on context"""
    if context == "medical":
        return ErrorMessages.MEDICAL_ERROR
    elif context == "nested_calls":
        return ErrorMessages.MAX_NESTED_CALLS
    return f"{ErrorMessages.GENERIC_ERROR} Error: {str(error)}"