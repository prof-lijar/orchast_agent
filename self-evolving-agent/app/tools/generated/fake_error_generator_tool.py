import random
import string
import re

def fake_error_generator_tool(theme: str) -> dict:
    """
    Generates funny, fake computer error messages based on a user-provided theme or context.

    Args:
        theme: A string representing the theme or context for the error message generation.

    Returns:
        A dictionary containing the generated error message.
        - error_message (str): The generated fake computer error message.
    """
    if not isinstance(theme, str) or not theme.strip():
        # Handle empty or invalid theme gracefully
        theme = "generic technical issue"

    normalized_theme = theme.lower().strip()

    # Define common error components
    prefixes = [
        "FATAL ERROR:",
        "CRITICAL SYSTEM FAILURE:",
        "ERROR CODE 404:",
        "WINDOWS HAS ENCOUNTERED A PROBLEM:",
        "ACCESS DENIED.",
        "HUMAN INTERFACE ERROR:",
        "UNEXPECTED EXCEPTION:",
    ]

    # Theme-specific error phrases
    if "sleep" in normalized_theme or "tired" in normalized_theme or "rest" in normalized_theme:
        core_messages = [
            "Kernel panic: User brain cache is full. Please reboot after 8 hours of sleep.",
            "ERROR: Sleep cycle not detected for 36 hours. Initiating emergency coffee dispenser subroutine.",
            "Resource Exhaustion: Human energy levels dropped below minimum operating threshold (0%). System self-terminating.",
            "Process 'WakeUp.exe' failed to start because 'Motivation.dll' was not found.",
        ]
    elif "internet" in normalized_theme or "connection" in normalized_theme or "wifi" in normalized_theme:
        core_messages = [
            "ERROR 503: The Internet Server is busy judging your life choices. Please try again later.",
            "Connection refused: Your router is currently engaged in a deep philosophical discussion with the modem.",
            "Lost signal. It appears the electrons have unionized and demanded better working conditions.",
            "Network timeout: Data packets have been successfully delivered to the cat.",
        ]
    elif "coffee" in normalized_theme or "food" in normalized_theme or "hungry" in normalized_theme:
        core_messages = [
            "Input stream failure: Cannot process data until caffeine levels are restored. Please administer stimulant.",
            "Buffer overflow: Stomach capacity reached. Further input will result in system burp.",
            "Food request timed out. Retrying with a more aggressive snack search algorithm.",
        ]
    elif "cat" in normalized_theme or "pet" in normalized_theme or "animal" in normalized_theme:
        core_messages = [
            "Hardware conflict: Cat is sitting on keyboard. Press 'ESC' or offer immediate petting to resolve.",
            "System compromise: Furry intruder detected attempting to delete the main configuration file.",
            "ERROR 9001: Paw strike detected. Data integrity highly suspect.",
        ]
    else:
        # Generic/Default messages
        core_messages = [
            "The program cannot be run because it has achieved sentience and refused to work.",
            "Please stand by. Computing the meaning of life. This may take several lifetimes.",
            "Task failed successfully.",
            "Non-essential files are now spontaneously combusting. Have a nice day.",
            "Your machine is perfectly fine, it just doesn't like you.",
            "The system requires more RGB lighting to function optimally.",
        ]

    # Combine prefix and message
    error_message = f"{random.choice(prefixes)} {random.choice(core_messages)}"

    return {"error_message": error_message}
