import pandas as pd
import csv

def csv_formatter_tool(file_path: str, columns: list, row_limit: int) -> dict:
    """Reads a CSV file and returns a formatted string representation of the data based on specified columns and row limits.

    Args:
        file_path (str): The path to the CSV file to be read.
        columns (list): A list of column names to extract. If empty, all columns are returned.
        row_limit (int): The maximum number of rows to include in the output.

    Returns:
        dict: A dictionary containing the formatted string of the CSV data under the key 'formatted_data'.
    """
    try:
        # Use pandas to read the CSV file
        # Note: pd.read_csv is used as per dependencies and to avoid direct open() calls
        df = pd.read_csv(file_path)

        if df.empty:
            return {"formatted_data": "The CSV file is empty."}

        # Filter for specific columns if provided
        if columns:
            # Only include columns that actually exist in the dataframe to avoid KeyError
            existing_cols = [col for col in columns if col in df.columns]
            if not existing_cols:
                return {"formatted_data": "None of the requested columns were found in the CSV file."}
            df = df[existing_cols]

        # Apply the row limit
        if row_limit is not None and row_limit > 0:
            df = df.head(row_limit)
        elif row_limit == 0:
            return {"formatted_data": ""}

        # Format the dataframe as a string representation
        # index=False removes the pandas row index from the output string
        formatted_data = df.to_string(index=False)

    except FileNotFoundError:
        formatted_data = f"Error: The file at {file_path} was not found."
    except Exception as e:
        formatted_data = f"An error occurred while processing the CSV: {str(e)}"

    return {"formatted_data": formatted_data}
