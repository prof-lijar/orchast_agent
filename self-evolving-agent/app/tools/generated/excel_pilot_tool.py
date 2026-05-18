import pandas as pd
import re
import os

def excel_pilot_tool(file_path: str, request: str) -> dict:
    """Analyzes Excel files and performs data processing or calculations based on a natural language request.

    Args:
        file_path (str): The path to the Excel file to be analyzed.
        request (str): The natural language request describing the calculation or processing needed.

    Returns:
        dict: A dictionary containing the 'result' of the operation as a string.
    """
    if not file_path or not request:
        return {"result": "Error: Please provide both a file path and a request."}

    # Check if the file exists before attempting to read
    if not os.path.exists(file_path):
        return {"result": f"Error: File not found at path: {file_path}"}

    try:
        # Load the Excel file using pandas
        df = pd.read_excel(file_path)
    except Exception as e:
        return {"result": f"Error reading Excel file: {str(e)}"}

    # Normalize request for easier parsing
    req = request.lower().strip()
    columns = df.columns.tolist()

    def find_best_column(query: str) -> str:
        """Finds the best matching column name from the dataframe columns.
        
        Args:
            query (str): The column name or phrase extracted from the request.
            
        Returns:
            str: The actual column name from the dataframe if found, otherwise None.
        """
        query = query.strip().lower()
        # 1. Exact match
        for col in columns:
            if col.lower() == query:
                return col
        # 2. Is the query a subset of the column name? (e.g., "sales" in "Total Sales")
        for col in columns:
            if query in col.lower():
                return col
        # 3. Is the column name a subset of the query? (e.g., "Total Sales" in "total sales for all items")
        for col in columns:
            if col.lower() in query:
                return col
        return None

    # Priority 1: Check for Grouped Operations
    # Pattern: (operation) (column) (groupby_keyword) (group_column)
    # Examples: "average unit price for each category", "total sales by region"
    grouped_pattern = r'(sum|total|average|mean)\s+(?:of\s+)?([\w\s]+?)\s+(?:for\s+each|by|per)\s+([\w\s]+)'
    grouped_match = re.search(grouped_pattern, req)
    
    if grouped_match:
        op, col_name, group_name = grouped_match.groups()
        target_col = find_best_column(col_name)
        group_col = find_best_column(group_name)
        
        if target_col and group_col:
            try:
                if op in ['sum', 'total']:
                    res = df.groupby(group_col)[target_col].sum()
                else:
                    res = df.groupby(group_col)[target_col].mean()
                return {"result": res.to_string()}
            except Exception as e:
                return {"result": f"Calculation error: {str(e)}"}
        else:
            missing = []
            if not target_col: missing.append(f"'{col_name}'")
            if not group_col: missing.append(f"'{group_name}'")
            return {"result": f"Could not find columns matching: {', '.join(missing)}"}

    # Priority 2: Check for Simple Operations
    # Pattern: (operation) (column)
    # Examples: "total sales", "average price", "sum of quantity"
    simple_pattern = r'(sum|total|average|mean)\s+(?:of\s+)?([\w\s]+)'
    simple_match = re.search(simple_pattern, req)
    
    if simple_match:
        op, col_name = simple_match.groups()
        # Remove common filler phrases from the extracted column name to improve matching
        clean_col_name = re.sub(r'\s+(for\s+all\s+items|in\s+total|overall)$', '', col_name, flags=re.IGNORECASE)
        target_col = find_best_column(clean_col_name)
        
        if target_col:
            try:
                if op in ['sum', 'total']:
                    res = df[target_col].sum()
                else:
                    res = df[target_col].mean()
                return {"result": str(res)}
            except Exception as e:
                return {"result": f"Calculation error: {str(e)}"}
        else:
            return {"result": f"Could not find a column matching '{clean_col_name}'."}

    # Priority 3: Default response for unsupported requests
    return {"result": "I couldn't identify a specific calculation (like sum or average) in your request. Please try 'What is the total [column]?' or 'What is the average [column] for each [category]?'"}
