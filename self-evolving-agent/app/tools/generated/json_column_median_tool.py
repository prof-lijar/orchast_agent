import json
import statistics

def json_column_median_tool(records_json: str, column_name: str) -> dict:
    """
    Calculates the median of a specified numerical column within a JSON array of objects.

    Ignores records that do not contain the column or where the value is not a number.

    Args:
        records_json: A JSON string representing an array of objects (e.g., '[{"data": 10}, {"data": 20}]').
        column_name: The name of the column (key) whose numerical values should be used for median calculation.

    Returns:
        A dictionary containing the calculated median: {"median": float}.
        Returns {"median": 0.0} if the input is invalid (non-array JSON, decode error) or if no numerical values are found.
    """
    try:
        records = json.loads(records_json)
    except json.JSONDecodeError:
        # Invalid JSON input
        return {"median": 0.0}

    if not isinstance(records, list):
        # Expected input is an array of records
        return {"median": 0.0}

    numerical_values = []

    for record in records:
        if isinstance(record, dict):
            value = record.get(column_name)

            # Check if the value is an integer or float
            if isinstance(value, (int, float)):
                numerical_values.append(float(value))

    if not numerical_values:
        # If no valid numerical values were found
        return {"median": 0.0}

    # Calculate the median
    calculated_median = statistics.median(numerical_values)

    return {"median": calculated_median}
