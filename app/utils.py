import datetime

def validate_booking_dates(start_time: datetime, end_time: datetime):
    """
    Validates the booking dates, ensuring that the start time is before the end time
    and that both are in the future.
    """
    now = datetime.datetime.utcnow()
    if start_time < now or end_time < now:
        return False, "Booking times must be in the future."
    if start_time >= end_time:
        return False, "Start time must be before end time."
    return True, ""
