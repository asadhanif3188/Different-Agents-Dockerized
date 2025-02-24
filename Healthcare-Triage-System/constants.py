from enum import Enum, StrEnum

class UrgencyLevel(StrEnum):
    """Enum for medical urgency levels"""
    ROUTINE = 'routine'
    URGENT = 'urgent'
    EMERGENCY = 'emergency'

class AppointmentType(StrEnum):
    """Enum for appointment types"""
    VIRTUAL = 'virtual'
    IN_PERSON = 'in-person'
    SPECIALIST = 'specialist'

class ModelType(StrEnum):
    """Enum for AI model types"""
    BASIC = 'CHEAP'
    ADVANCED = 'EXPENSIVE'
#test
class ErrorMessages:
    """Error message constants"""
    MAX_NESTED_CALLS = 'Complex medical inquiry detected - please speak with a healthcare provider directly'
    GENERIC_ERROR = 'I apologize, but I encountered an error. Please try rephrasing your question.'
    MEDICAL_ERROR = 'I apologize, but I encountered an error. For medical questions, please consult with a healthcare provider.'

class UI:
    """UI-related constants"""
    TITLE = '🏥 AI-Powered Healthcare Triage Assistant'
    DISCLAIMER = '''
        ⚕️ Medical Disclaimer: This is a triage assistant only. 
        For emergencies, call 911 or your local emergency services immediately.
        This system does not replace professional medical advice.
    '''

# Additional constants if needed
VALID_MESSAGE_TYPES = ['human', 'ai', 'system']
MAX_RETRY_ATTEMPTS = 3
DEFAULT_MESSAGE_HISTORY = 3