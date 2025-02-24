import os
import json
from typing import List, Generator
from langchain_groq import ChatGroq
from langchain_community.llms import Ollama
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from utils import get_latest_messages, load_settings, format_error_response
from tools import estimate_wait_time
from constants import UrgencyLevel, ModelType


def decide_model_from_prompt(messages: List[dict]) -> str:
    """
    Uses a lightweight model to determine if the medical inquiry needs the more powerful model
    """
    settings = load_settings()
    router = Ollama(model=os.getenv('OLLAMA_MODEL'))
    latest_messages = get_latest_messages(messages)

    router_prompt = settings['prompts'][
                        'router_prompt'] + f"\n\nRecent conversation:\n{latest_messages}\n\nOutput only: CHEAP or EXPENSIVE"

    response = router.invoke(router_prompt)
    return response.strip()


def prompt_ai(messages: List[dict], router_decided_model: str, nested_calls: int = 0) -> Generator[str, None, None]:
    """
    Main function to handle medical inquiries and tool usage
    Args:
        messages: List of conversation messages
        router_decided_model: Model type decision from router
        nested_calls: Counter for nested function calls
    Yields:
        str: Response chunks
    """
    settings = load_settings()
    if nested_calls > settings['system']['max_nested_calls']:
        yield format_error_response(Exception(), "nested_calls")
        return

    latest_message = messages[-1].content.lower()

    # Handle common queries directly with tools
    if "wait time" in latest_message:
        wait_time_result = estimate_wait_time(UrgencyLevel.ROUTINE)
        yield wait_time_result
        return

    if "assess" in latest_message and "symptoms" in latest_message:
        yield "I'll help assess your symptoms. Please describe your specific symptoms, how long you've had them, and their severity (mild/moderate/severe)."
        return

    try:
        if router_decided_model.lower() == ModelType.BASIC:
            # Use Ollama for basic queries
            ai_agent = Ollama(model=os.getenv('OLLAMA_MODEL'))
            for chunk in ai_agent.stream(messages[-1].content):
                yield str(chunk)
        else:
            # Use Groq for complex medical queries
            groq = ChatGroq(
                api_key=os.getenv('GROQ_API_KEY'),
                model_name=os.getenv('GROQ_MODEL')
            )
            system_msg = settings['prompts']['system_message']
            response = SystemMessage(content=system_msg)
            yield response.content

    except Exception as e:
        yield format_error_response(e, "medical")