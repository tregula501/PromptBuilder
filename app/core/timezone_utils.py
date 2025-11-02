"""
Timezone utilities for PromptBuilder.

Handles timezone conversions for game times and other datetime operations.
"""

from datetime import datetime
from typing import Optional
import logging
from zoneinfo import ZoneInfo, available_timezones
import platform

logger = logging.getLogger(__name__)


def get_system_timezone() -> str:
    """
    Get the system's current timezone.

    Returns:
        str: System timezone name (e.g., 'America/New_York')
    """
    try:
        # For Windows, try to get timezone from datetime
        if platform.system() == "Windows":
            import time
            # Get the timezone name
            if time.daylight:
                tz_name = time.tzname[1]
            else:
                tz_name = time.tzname[0]

            # Map common Windows timezone abbreviations to IANA names
            windows_tz_map = {
                "EST": "America/New_York",
                "EDT": "America/New_York",
                "CST": "America/Chicago",
                "CDT": "America/Chicago",
                "MST": "America/Denver",
                "MDT": "America/Denver",
                "PST": "America/Los_Angeles",
                "PDT": "America/Los_Angeles",
            }

            if tz_name in windows_tz_map:
                return windows_tz_map[tz_name]

        # Fallback: use UTC offset to guess timezone
        import time
        utc_offset = -time.timezone / 3600
        offset_map = {
            -5: "America/New_York",
            -6: "America/Chicago",
            -7: "America/Denver",
            -8: "America/Los_Angeles",
        }

        if utc_offset in offset_map:
            return offset_map[utc_offset]

    except Exception as e:
        logger.warning(f"Could not determine system timezone: {e}")

    # Default fallback
    return "America/New_York"


def get_common_us_timezones() -> list[str]:
    """
    Get list of common US timezones for UI selection.

    Returns:
        list: List of timezone names
    """
    return [
        "America/New_York",      # Eastern
        "America/Chicago",       # Central
        "America/Denver",        # Mountain
        "America/Phoenix",       # Arizona (no DST)
        "America/Los_Angeles",   # Pacific
        "America/Anchorage",     # Alaska
        "Pacific/Honolulu",      # Hawaii
        "UTC",                   # UTC
    ]


def convert_to_timezone(dt: Optional[datetime], target_tz: str) -> Optional[datetime]:
    """
    Convert a datetime to the target timezone.

    Args:
        dt: Datetime to convert (can be naive or aware)
        target_tz: Target timezone name (e.g., 'America/New_York')

    Returns:
        Optional[datetime]: Datetime converted to target timezone, or None if input is None
    """
    if dt is None:
        return None

    try:
        target_zone = ZoneInfo(target_tz)

        # If datetime is naive, assume it's UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))

        # Convert to target timezone
        return dt.astimezone(target_zone)

    except Exception as e:
        logger.error(f"Error converting datetime to {target_tz}: {e}")
        return dt


def format_game_time(
    dt: Optional[datetime],
    timezone: str,
    format_string: str = "%a %I:%M %p %Z"
) -> str:
    """
    Format a game time for display with timezone conversion.

    Args:
        dt: Datetime to format
        timezone: Timezone to display in
        format_string: strftime format string (default includes timezone abbreviation)

    Returns:
        str: Formatted time string or "Time TBD" if dt is None
    """
    if dt is None:
        return "Time TBD"

    # Convert to target timezone
    converted = convert_to_timezone(dt, timezone)

    if converted is None:
        return "Time TBD"

    try:
        return converted.strftime(format_string)
    except Exception as e:
        logger.error(f"Error formatting datetime: {e}")
        return dt.strftime("%a %I:%M %p")


def is_valid_timezone(tz_name: str) -> bool:
    """
    Check if a timezone name is valid.

    Args:
        tz_name: Timezone name to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        ZoneInfo(tz_name)
        return True
    except Exception:
        return False


def get_all_timezones() -> list[str]:
    """
    Get all available timezone names.

    Returns:
        list: Sorted list of all available timezone names
    """
    return sorted(available_timezones())
