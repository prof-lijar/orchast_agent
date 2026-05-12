import datetime
import math

def fortune_teller_tool(birthdate: str) -> dict:
    """
    Generates a fictional fortune based on a user's birthdate using deterministic pseudo-random logic.
    
    Args:
        birthdate (str): The user's birthdate in 'YYYY-MM-DD' format.
        
    Returns:
        dict: A dictionary containing the 'fortune' string.
    """
    # Default fortune for invalid dates
    default_fortune = "The stars are unclear. Please provide a valid birthdate."
    
    if not birthdate or not isinstance(birthdate, str):
        return {"fortune": default_fortune}
    
    try:
        # Parse the birthdate
        parsed_date = datetime.datetime.strptime(birthdate, "%Y-%m-%d")
        
        # Extract components for pseudo-random logic
        year = parsed_date.year
        month = parsed_date.month
        day = parsed_date.day
        
        # Create a deterministic seed based on the date
        seed = year * 10000 + month * 100 + day
        
        # Define some fictional fortunes
        fortunes = [
            "A great adventure awaits you!",
            "Love is in the air for you today.",
            "Your hard work will soon pay off.",
            "A new opportunity is coming your way.",
            "Stay cautious with your finances.",
            "Health and happiness are your best friends.",
            "Trust your intuition; it will guide you right.",
            "Unexpected news will bring you joy.",
            "Focus on your goals; success is near.",
            "Kindness will return to you tenfold."
        ]
        
        # Use a simple pseudo-random selection based on the seed
        index = abs(hash(str(seed))) % len(fortunes)
        fortune = fortunes[index]
        
        return {"fortune": fortune}
        
    except ValueError:
        # Handle invalid date format
        return {"fortune": default_fortune}
