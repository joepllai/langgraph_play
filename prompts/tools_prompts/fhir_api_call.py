"""
Prompts for the FHIR API call tool that handles direct API interactions.
"""

FHIR_API_PROMPTS = {
    "ERROR_MESSAGES": {
        "REQUEST_FAILED": "Failed to process FHIR request: {error}",
        "INVALID_PARAMS": "Invalid parameters provided: {error}",
        "API_ERROR": "API request failed: {error}",
        "TIMEOUT": "Request timed out after {timeout} seconds"
    },

    "VALIDATION": {
        "REQUIRED_FIELDS": ["resource_type"],
        "VALID_RESOURCES": [
            "Patient", "Observation", "Condition",
            "Procedure", "Medication", "Encounter"
        ]
    },

    "RESPONSE_FORMAT": {
        "SUCCESS": {
            "status": "success",
            "data": "{data}"
        },
        "ERROR": {
            "status": "error",
            "data": None,
            "error": "{error}"
        }
    }
}
