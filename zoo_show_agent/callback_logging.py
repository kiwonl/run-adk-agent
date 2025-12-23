
import logging
import google.cloud.logging

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest


# Callback to log the user query sent to the model.
def log_query_to_model(callback_context: CallbackContext, llm_request: LlmRequest):
    """
    Logs the user query sent to the model.

    Args:
        callback_context (CallbackContext): The callback context information.
        llm_request (LlmRequest): The request object sent to the model.
    """
    # Log only if there is request content and the last role is 'user'.
    if llm_request.contents and llm_request.contents[-1].role == "user":
        if llm_request.contents[-1].parts[-1].text:
            last_user_message = llm_request.contents[-1].parts[0].text
            logging.info(
                f"🗣️ [Query to {callback_context.agent_name}]: " + last_user_message
            )


# Callback to log the model's response.
def log_model_response(callback_context: CallbackContext, llm_response: LlmResponse):
    """
    Logs the response from the model.

    Args:
        callback_context (CallbackContext): The callback context information.
        llm_response (LlmResponse): The response object from the model.
    """
    # Log only if there is response content and parts.
    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if part.text:
                logging.info(
                    f"🤖 [Response from {callback_context.agent_name}]: " + part.text
                )
            elif part.function_call:
                logging.info(
                    f"🛠️ [Function Call from {callback_context.agent_name}]: "
                    + part.function_call.name
                )

