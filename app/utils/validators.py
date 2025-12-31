import os

def validate_directory_path(path):
    """Checks if a directory path exists and is a directory."""
    if not path or not os.path.exists(path):
        return False, "Path does not exist."
    if not os.path.isdir(path):
        return False, "Path is not a directory."
    return True, ""

def validate_metric(value):
    """Checks if metric is a positive float."""
    try:
        val = float(value)
        if val <= 0:
            return False, "Metric must be positive."
        return True, ""
    except ValueError:
        return False, "Metric must be a number."
