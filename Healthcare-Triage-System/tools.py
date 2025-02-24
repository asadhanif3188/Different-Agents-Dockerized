import json
from typing import List, Optional
from langchain_core.tools import tool
from database import db
from utils import analyze_symptoms_severity, validate_appointment_request
from constants import UrgencyLevel, AppointmentType


@tool
def check_symptoms(symptoms: List[str], duration: str, severity: str) -> str:
    """
    Records and analyzes patient symptoms
    Args:
        symptoms: List of reported symptoms
        duration: How long symptoms have been present
        severity: Perceived severity (mild/moderate/severe)
    Returns:
        str: Initial assessment and recommendations
    """
    symptom_record = db.add_symptoms(symptoms, duration, severity)

    if analyze_symptoms_severity(symptoms, severity):
        return "URGENT: Please seek immediate medical attention or call emergency services."

    return json.dumps({
        "assessment": "Symptoms recorded and assessed",
        "record_id": symptom_record["id"],
        "recommendation": "Based on initial assessment, scheduling a consultation is recommended."
    })


@tool
def schedule_appointment(
        appointment_type: AppointmentType,
        preferred_date: str,
        symptoms_record_id: Optional[int] = None
) -> str:
    """
    Schedules a healthcare appointment
    Args:
        appointment_type: Type of appointment needed
        preferred_date: Preferred date for appointment
        symptoms_record_id: Optional reference to recorded symptoms
    Returns:
        str: Appointment confirmation or available slots
    """
    try:
        validate_appointment_request(appointment_type, preferred_date)
        appointment = db.add_appointment(appointment_type, preferred_date, symptoms_record_id)

        return json.dumps({
            "status": "confirmed",
            "appointment_details": appointment,
            "instructions": "Please arrive 15 minutes before your appointment time."
        })
    except Exception as e:
        return f"Error scheduling appointment: {str(e)}"


@tool
def get_medical_history(patient_id: str) -> str:
    """
    Retrieves patient's medical history
    Args:
        patient_id: Patient's identifier
    Returns:
        str: JSON string of medical history
    """
    history = db.get_medical_history(patient_id)
    return json.dumps(history)


@tool
def estimate_wait_time(urgency_level: UrgencyLevel) -> str:
    """
    Estimates current wait time based on urgency
    Args:
        urgency_level: Level of medical urgency
    Returns:
        str: Estimated wait time
    """
    with open('settings.yaml', 'r') as f:
        settings = yaml.safe_load(f)
        wait_times = {
            level: data['wait_time']
            for level, data in settings['triage']['urgency_levels'].items()
        }

    return json.dumps({
        "urgency": urgency_level,
        "estimated_wait": wait_times[urgency_level],
        "note": "Wait times are estimates and may vary based on current patient volume"
    })