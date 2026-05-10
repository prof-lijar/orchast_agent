import json
import statistics
import math
from statistics import StatisticsError

def json_column_describe_tool(records_json: str, column_name: str) -> dict:
    """
    Calculates summary statistics (count, mean, min, max, and sample standard deviation) 
    for a specified numerical column in a JSON array of objects.

    Ignores records that do not contain the column or where the value is not a number.

    Args:
        records_json: A JSON string representing an array of objects (e.g., '[{"data": 10}, {"data": 20}]').
        column_name: The name of the column (key) whose numerical values should be analyzed.

    Returns:
        A dictionary containing the calculated statistics: 
        {"count": int, "mean": float, "stdev": float, "min": float, "max": float}.
        Returns default values (count=0, others=0.0) if input is invalid or no numerical data is found.
    """
    default_output = {
        "count": 0,
        "mean": 0.0,
        "stdev": 0.0,
        "min": 0.0,
        "max": 0.0
    }

    try:
        records = json.loads(records_json)
    except json.JSONDecodeError:
        return default_output

    if not isinstance(records, list):
        return default_output

    numerical_values = []

    for record in records:
        if isinstance(record, dict):
            value = record.get(column_name)

            # Check if the value is an integer or float
            if isinstance(value, (int, float)):
                numerical_values.append(float(value))

    count = len(numerical_values)

    if count == 0:
        return default_output

    # Calculate basic statistics
    data_min = min(numerical_values)
    data_max = max(numerical_values)
    data_mean = statistics.mean(numerical_values)

    # Calculate sample standard deviation (stdev)
    data_stdev = 0.0
    if count >= 2:
        try:
            data_stdev = statistics.stdev(numerical_values)
        except StatisticsError:
            # Should only happen if all values are identical (stdev is 0.0), but handled
            # for completeness. The stdev function handles the identical case correctly.
            pass
    
    # If count is 1, stdev remains 0.0 as initialized.

    return {
        "count": count,
        "mean": data_mean,
        "stdev": data_stdev,
        "min": data_min,
        "max": data_max
    }
