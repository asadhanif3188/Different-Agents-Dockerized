import streamlit as st
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict, Optional
from langchain_groq import ChatGroq
from langchain_community.llms import Ollama
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage
import pytz
from enum import Enum


# Enums for standardization
class UrgencyLevel(str, Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class AppointmentType(str, Enum):
    VIRTUAL = "virtual"
    IN_PERSON = "in-person"
    SPECIALIST = "specialist"


# Environment and configuration
groq_api_key = os.getenv('GROQ_API_KEY', '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')
groq_model = os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768')
ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
timezone = pytz.timezone('America/New_York')

# Mock database for healthcare system
mock_healthcare_db = {
    "appointments": [],
    "triage_records": [],
    "available_slots": {
        "virtual": ["09:00", "10:00", "14:00", "15:00"],
        "in-person": ["11:00", "13:00", "16:00"],
        "specialist": ["10:30", "14:30"]
    },
    "symptoms_history": []
}


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Healthcare Triage Tools
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
    symptom_record = {
        "id": len(mock_healthcare_db["symptoms_history"]) + 1,
        "symptoms": symptoms,
        "duration": duration,
        "severity": severity,
        "recorded_at": str(datetime.now(timezone)),
    }
    mock_healthcare_db["symptoms_history"].append(symptom_record)

    # Basic severity check for demonstration
    if severity.lower() == "severe" or any(urgent in [s.lower() for s in symptoms]
                                           for urgent in ["chest pain", "difficulty breathing", "severe pain"]):
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
        date_obj = datetime.strptime(preferred_date, "%Y-%m-%d").date()

        # Mock appointment scheduling logic
        appointment = {
            "id": len(mock_healthcare_db["appointments"]) + 1,
            "type": appointment_type,
            "date": preferred_date,
            "time": mock_healthcare_db["available_slots"][appointment_type][0],
            "symptoms_record_id": symptoms_record_id,
            "scheduled_at": str(datetime.now(timezone))
        }

        mock_healthcare_db["appointments"].append(appointment)
        mock_healthcare_db["available_slots"][appointment_type].pop(0)

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
    Retrieves patient's medical history (mock data)
    Args:
        patient_id: Patient's identifier
    Returns:
        str: JSON string of medical history
    """
    # Mock medical history - in real implementation, this would query a secure database
    return json.dumps({
        "recent_visits": ["2024-01-15: Regular checkup", "2023-12-01: Flu symptoms"],
        "ongoing_conditions": ["Mild hypertension"],
        "allergies": ["Penicillin"],
        "current_medications": ["Lisinopril 10mg daily"]
    })


@tool
def estimate_wait_time(urgency_level: UrgencyLevel) -> str:
    """
    Estimates current wait time based on urgency
    Args:
        urgency_level: Level of medical urgency
    Returns:
        str: Estimated wait time
    """
    wait_times = {
        UrgencyLevel.ROUTINE: "2-3 hours",
        UrgencyLevel.URGENT: "30-45 minutes",
        UrgencyLevel.EMERGENCY: "Immediate attention"
    }
    return json.dumps({
        "urgency": urgency_level,
        "estimated_wait": wait_times[urgency_level],
        "note": "Wait times are estimates and may vary based on current patient volume"
    })


# Available functions mapping
available_functions = {
    "check_symptoms": check_symptoms,
    "schedule_appointment": schedule_appointment,
    "get_medical_history": get_medical_history,
    "estimate_wait_time": estimate_wait_time
}


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Enhanced AI Router for Healthcare
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def get_latest_messages(messages: List[dict], num_messages: int = 3) -> str:
    """Gets the latest n messages from the conversation history"""
    return "\n\n".join([message.content for message in messages[-num_messages:]])


def decide_model_from_prompt(messages: List[dict]) -> str:
    """
    Strict router to determine query complexity
    """
    router = Ollama(model=ollama_model)
    latest_message = messages[-1].content.lower()

    # First check for explicit simple queries
    simple_queries = [
        "routine checkup",
        "schedule appointment",
        "wait time",
        "office hours",
        "where is",
        "directions",
        "mild cold",
        "registration",
    ]

    # If any simple query patterns match, return CHEAP immediately
    if any(phrase in latest_message for phrase in simple_queries):
        return "CHEAP"

    # Check for complex/emergency patterns
    complex_queries = [
        "severe",
        "emergency",
        "chest pain",
        "difficulty breathing",
        "multiple symptoms",
        "drug interaction",
        "mental health",
        "suicidal",
        "confusion",
        "elderly",
        "pregnancy",
    ]

    # If any complex patterns match, route to EXPENSIVE
    if any(phrase in latest_message for phrase in complex_queries):
        return "EXPENSIVE"

    # For anything else, use the LLM router as backup
    router_prompt = """
    Classify this medical query as either 'CHEAP' (simple) or 'EXPENSIVE' (complex).

    CHEAP = routine/administrative tasks like:
    - Scheduling routine checkups
    - Basic appointments
    - Wait times
    - Location/hours
    - Simple symptoms

    EXPENSIVE = medical complexity like:
    - Multiple symptoms
    - Severe conditions
    - Mental health
    - Complex conditions
    - Emergencies

    Query: {latest_message}

    Output exactly one word - CHEAP or EXPENSIVE:"""

    try:
        response = router.invoke(router_prompt.format(latest_message=latest_message))
        cleaned_response = response.strip().upper()
        return "CHEAP" if "CHEAP" in cleaned_response else "EXPENSIVE"
    except Exception as e:
        print(f"Router LLM error: {str(e)}")
        # Default to CHEAP for basic queries if LLM fails
        return "CHEAP"


def prompt_ai(messages: List[dict], router_decided_model: str, nested_calls: int = 0):
    """
    Enhanced function to handle medical inquiries with visible model routing
    """
    if nested_calls > 3:
        yield "Error: Too many nested calls. Please try rephrasing your question."
        return

    latest_message = messages[-1].content.lower()

    # Handle simple queries directly
    simple_queries = {
        "wait time": (estimate_wait_time, {"urgency_level": UrgencyLevel.ROUTINE}),
        "schedule": (schedule_appointment, {"appointment_type": AppointmentType.VIRTUAL,
                                            "preferred_date": datetime.now().strftime("%Y-%m-%d")}),
        "routine checkup": (schedule_appointment, {"appointment_type": AppointmentType.IN_PERSON,
                                                   "preferred_date": datetime.now().strftime("%Y-%m-%d")})
    }

    # First yield the routing decision with clear indication
    if router_decided_model.lower() == "cheap":
        yield "🔵 Using Ollama Model for Simple Query\n\n"

        # Try to use Ollama
        try:
            ai_agent = Ollama(model=ollama_model)
            response = ai_agent.invoke(messages[-1].content)
            yield str(response)
        except Exception as e:
            yield f"Error with Ollama model: {str(e)}\n"
            yield "Falling back to basic response handler...\n"

            # Handle basic queries with tools
            for key, (tool_func, params) in simple_queries.items():
                if key in latest_message:
                    try:
                        result = tool_func(**params)
                        yield str(result)
                        return
                    except Exception as tool_error:
                        yield f"Error using tool: {str(tool_error)}"

    else:
        yield "🔴 Using Groq Model for Complex Query\n\n"
        try:
            groq_agent = ChatGroq(
                api_key=groq_api_key,
                model_name=groq_model
            )
            response = groq_agent.invoke(messages[-1].content)
            yield str(response)
        except Exception as e:
            yield f"Error with Groq model: {str(e)}\nPlease consult a healthcare provider for complex medical questions."

def main():
    st.title("🏥 AI-Powered Healthcare Triage Assistant")

    # Initialize session state
    if "messages" not in st.session_state:
        system_message = f"""
        You are an AI healthcare triage assistant with two-tier processing:

        Simple Queries (Basic Model):
        - Routine appointment scheduling
        - Facility information
        - Basic health advice
        - Wait time inquiries
        - Minor symptoms (common cold, etc.)

        Complex/Urgent Queries (Advanced Model):
        - Multiple symptom assessment
        - Chest pain or breathing issues
        - Mental health concerns
        - Medication interactions
        - Complex medical conditions
        - Urgent care needs
        - Pediatric/elderly concerns

        Critical Guidelines:
        - ALWAYS refer emergency situations to immediate medical care
        - Maintain professional, empathetic communication
        - Protect patient privacy
        - Be clear about AI limitations
        - Recommend healthcare provider consultation when in doubt

        Current date and time: {datetime.now(timezone).strftime('%Y-%m-%d %H:%M %Z')}
        """
        st.session_state["messages"] = [SystemMessage(content=system_message)]

    # Example Queries at the top of UI
    with st.expander("📋 Example Queries", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🔵 Simple Queries (Ollama Model)")
            st.markdown("""
            1. "What's the current wait time?"
            2. "I need to schedule a routine checkup"
            3. "Where is the nearest clinic located?"
            4. "What are your office hours?"
            5. "I have a mild cold and runny nose"
            """)

        with col2:
            st.markdown("### 🔴 Complex Queries (Groq Model)")
            st.markdown("""
            1. "Severe chest pain and difficulty breathing"
            2. "Multiple symptoms: fever, joint pain, and rash"
            3. "Concerns about drug interactions with my medications"
            4. "Elderly parent showing signs of confusion"
            5. "Recurring migraines with new symptoms"
            """)

    # Medical Disclaimer
    st.warning("""
        ⚕️ Emergency Warning: If you're experiencing life-threatening symptoms,
        call 911 or your local emergency number immediately.
        This system does not replace professional medical advice.
    """)

    # Display chat history
    for message in st.session_state.messages:
        role = "assistant" if isinstance(message, (AIMessage, SystemMessage)) else "user"
        with st.chat_message(role):
            st.markdown(message.content)

    # Handle user input with visible routing
    if prompt := st.chat_input("Please describe your medical concern or request"):
        # Add user message to chat
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append(HumanMessage(content=prompt))

        # Process response
        with st.chat_message("assistant"):
            model_choice = decide_model_from_prompt(st.session_state.messages)

            # Show routing decision with clear visual indicator
            if model_choice.lower() == "cheap":
                st.info("🔵 Processing as Simple/Routine Query (Ollama Model)")
            else:
                st.warning("🔴 Processing as Complex/Critical Query (Groq Model)")

            response_text = ""
            for chunk in prompt_ai(st.session_state.messages, model_choice):
                response_text += str(chunk)
                st.write(chunk)

            st.session_state.messages.append(AIMessage(content=response_text))


if __name__ == "__main__":
    main()