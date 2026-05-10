# Define the fixed, simple 3-line high ASCII font mapping
# Each character is represented by a list of 3 strings (lines).
FONT = {
    'A': [" /\\  ", "/__\\ ", "A    "],
    'B': ["|==  ", "|==/ ", "|--\\ "],
    'C': [" /-- ", "/    ", "\----"],
    'D': ["|--\\ ", "|  | ", "|--/ "],
    'E': ["-----", "|====", "-----"],
    'F': ["-----", "|====", "|    "],
    'G': [" /-- ", "| /| ", " \-- "],
    'H': ["|  | ", "|--| ", "|  | "],
    'I': ["-----", "  |  ", "-----"],
    'J': ["  /  ", "  |  ", "---- "],
    'K': ["|/\\  ", "|  | ", "|\\ / "],
    'L': ["|    ", "|    ", "---- "],
    'M': ["/\\/\\ ", "| || ", "| || "],
    'N': ["|\\ | ", "| \\| ", "|  | "],
    'O': [" /\\  ", "|  | ", " \/  "],
    'P': ["-----", "|--/ ", "|    "],
    'Q': [" /\\  ", "|/\\| ", " \/ o"],
    'R': ["|--\\ ", "|  / ", "| \\  "],
    'S': [" /-- ", " --/ ", " /-- "],
    'T': ["-----", "  |  ", "  |  "],
    'U': ["|  | ", "|  | ", " \/  "],
    'V': ["\\  / ", " \\/  ", " V   "],
    'W': ["W  W ", " \\/\\ ", "  V  "],
    'X': ["\\ /  ", " X   ", "/ \\  "],
    'Y': ["\\ /  ", " |   ", " |   "],
    'Z': ["-----", "  /  ", "-----"],
    '1': ["  1  ", "  |  ", "-----"],
    '2': [" /-- ", " --/ ", "/----"],
    '3': ["/--\\ ", " --/ ", " \--/"],
    '4': ["|  | ", "|--| ", "   | "],
    '5': ["-----", "/----", "\----"],
    '6': [" /-- ", "|----", " \--/"],
    '7': ["-----", "   / ", "  /  "],
    '8': ["/--\\ ", "\--/ ", "/--\\ "],
    '9': ["/--\\ ", "\--| ", " \--/"],
    '0': ["/--\\ ", "|  | ", "\--/ "],
    ' ': ["     ", "     ", "     "],
    '!': ["  |  ", "  |  ", "  O  "],
    '?': [" /\\  ", " /   ", " O   "],
    '.': ["     ", "     ", "  .  "],
    '_DEFAULT_': [" ### ", " ### ", " ### "]
}
LINE_HEIGHT = 3

def text_to_ascii_art_tool(text: str) -> dict:
    """
    Converts input text into stylized ASCII art using a fixed, simple font mapping.

    Args:
        text: The string to convert to ASCII art.

    Returns:
        A dictionary containing the generated ASCII art.
            - ascii_art (str): The multi-line string representation of the ASCII art.
    """
    if not text:
        return {"ascii_art": ""}

    # Initialize lists to hold the components of each line (3 lines high)
    output_lines = [[] for _ in range(LINE_HEIGHT)]

    # Process the text character by character
    for char in text.upper():
        # Retrieve the ASCII art representation, falling back to a default if unknown
        art_char = FONT.get(char, FONT['_DEFAULT_'])
        
        # Append the corresponding line parts to the output lists
        for i in range(LINE_HEIGHT):
            output_lines[i].append(art_char[i])

    # Combine the lists of strings into final lines
    # rstrip() removes trailing whitespace from the combined lines
    final_lines = ["".join(line_parts).rstrip() for line_parts in output_lines]
    
    # Join the lines with newline characters
    ascii_art_output = "\n".join(final_lines)

    return {
        "ascii_art": ascii_art_output
    }
