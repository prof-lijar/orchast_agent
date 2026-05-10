import json
import statistics

def json_column_mean_tool(records_json: str, column_name: str) -> dict:
    """
    Calculates the arithmetic mean of a specified numerical column within a JSON array of objects.

    Ignores records that do not contain the column or where the value is not a number.

    Args:
        records_json: A JSON string representing an array of objects (e.g., '[{"data": 10}, {"data": 20}]').
        column_name: The name of the column (key) whose numerical values should be averaged.

    Returns:
        A dictionary containing the calculated mean: {"mean": float}.
        Returns {"mean": 0.0} if the input is invalid (non-array JSON, decode error) or if no numerical values are found.
    """
    try:
        records = json.loads(records_json)
    except json.JSONDecodeError:
        # Invalid JSON input
        return {"mean": 0.0}

    if not isinstance(records, list):
        # Expected input is an array of records
        return {"mean": 0.0}

    numerical_values = []

    for record in records:
        if isinstance(record, dict):
            value = record.get(column_name)

            # Check if the value is an integer or float
            if isinstance(value, (int, float)):
                numerical_values.append(float(value))

    if not numerical_values:
        # If no valid numerical values were found
        return {"mean": 0.0}

    # Calculate the mean
    calculated_mean = statistics.mean(numerical_values)

    return {"mean": calculated_mean}
