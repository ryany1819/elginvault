from datetime import datetime

def utc_string_to_local(utc_string):
    """
    Converts a UTC time string (e.g., '2000-01-01T00:00:00+00:00')
    to 'YYYY-MM-DD HH:mm:ss' format.
    """
    try:
        utc_datetime = datetime.fromisoformat(utc_string.replace('Z', '+00:00')) #replace Z to +00:00 to make fromisoformat work.
        local_string = utc_datetime.strftime('%Y-%m-%d %H:%M:%S')
        return local_string
    except ValueError:
        return None  # Handle invalid input