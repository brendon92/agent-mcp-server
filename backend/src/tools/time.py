from datetime import datetime
import dateutil.parser
import dateutil.tz

class TimeTools:
    def get_current_time(self, format: str = "long", timezone: str = "UTC") -> str:
        """
        Gets the current time in a specific format and timezone.
        
        Args:
            format: "short" (YYYY-MM-DD), "long" (Full string), "time" (HH:MM:SS)
            timezone: Timezone string (e.g., "UTC", "America/New_York", "Europe/London")
        """
        try:
            tz = dateutil.tz.gettz(timezone)
            if tz is None:
                return f"Error: Invalid timezone '{timezone}'"
                
            now = datetime.now(tz)
            
            if format == "short":
                return now.strftime("%Y-%m-%d")
            elif format == "time":
                return now.strftime("%H:%M:%S")
            else: # long or default
                return now.strftime("%Y-%m-%d %H:%M:%S %Z")
                
        except Exception as e:
            return f"Error getting time: {str(e)}"
