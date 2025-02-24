import json
from datetime import datetime
from typing import Dict, List, Any


class MockDatabase:
    def __init__(self):
        self._data = {
            "appointments": [],
            "triage_records": [],
            "symptoms_history": []
        }

        # Load initial available slots from config
        with open('config.json', 'r') as f:
            config = json.load(f)
            self._data["available_slots"] = config["mock_data"]["available_slots"]

    def add_symptoms(self, symptoms: List[str], duration: str, severity: str) -> Dict[str, Any]:
        """Add a new symptoms record"""
        record = {
            "id": len(self._data["symptoms_history"]) + 1,
            "symptoms": symptoms,
            "duration": duration,
            "severity": severity,
            "recorded_at": str(datetime.now()),
        }
        self._data["symptoms_history"].append(record)
        return record

    def add_appointment(self, appointment_type: str, date: str,
                        symptoms_record_id: int = None) -> Dict[str, Any]:
        """Add a new appointment"""
        if not self._data["available_slots"].get(appointment_type):
            raise ValueError(f"Invalid appointment type: {appointment_type}")

        if not self._data["available_slots"][appointment_type]:
            raise ValueError(f"No available slots for {appointment_type}")

        appointment = {
            "id": len(self._data["appointments"]) + 1,
            "type": appointment_type,
            "date": date,
            "time": self._data["available_slots"][appointment_type][0],
            "symptoms_record_id": symptoms_record_id,
            "scheduled_at": str(datetime.now())
        }

        self._data["appointments"].append(appointment)
        self._data["available_slots"][appointment_type].pop(0)
        return appointment

    def get_medical_history(self, patient_id: str) -> Dict[str, Any]:
        """Get patient medical history"""
        return {
            "recent_visits": ["2024-01-15: Regular checkup", "2023-12-01: Flu symptoms"],
            "ongoing_conditions": ["Mild hypertension"],
            "allergies": ["Penicillin"],
            "current_medications": ["Lisinopril 10mg daily"]
        }


# Create a singleton instance
db = MockDatabase()