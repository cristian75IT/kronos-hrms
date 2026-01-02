from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List, Set, Union

from src.shared.clients import ConfigClient, CalendarClient

class CalendarUtils:
    """Utilities for calendar calculations (working days, holidays, closures).
    
    Now primarily uses the Calendar microservice, with fallback to Config service.
    """

    def __init__(self, config_client: ConfigClient = None, calendar_client: CalendarClient = None):
        self.config_client = config_client or ConfigClient()
        self.calendar_client = calendar_client or CalendarClient()
        # Flag to control which service to use
        self._use_calendar_service = True

    async def get_system_config(self, key: str, default: Any = None) -> Any:
        return await self.config_client.get_sys_config(key, default)

    async def get_holidays(self, year: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[dict]:
        """Get holidays for a specific year, optionally filtering by date range."""
        if self._use_calendar_service:
            try:
                holidays = await self.calendar_client.get_holidays(year, start_date, end_date)
                if holidays:
                    return holidays
            except Exception:
                pass  # Fallback to config client
        return await self.config_client.get_holidays(year, start_date, end_date)

    async def get_company_closures(self, start_date: date, end_date: date) -> List[dict]:
        """Get company closures overlapping the date range, handling multiple years."""
        years = set()
        years.add(start_date.year)
        years.add(end_date.year)
        
        all_closures = []
        for year in years:
            closures = []
            if self._use_calendar_service:
                try:
                    closures = await self.calendar_client.get_closures(year)
                except Exception:
                    closures = await self.config_client.get_company_closures(year)
            else:
                closures = await self.config_client.get_company_closures(year)
            
            for closure in closures:
                closure_start = closure.get("start_date")
                closure_end = closure.get("end_date")
                if closure_start and closure_end:
                    try:
                        c_start = date.fromisoformat(closure_start) if isinstance(closure_start, str) else closure_start
                        c_end = date.fromisoformat(closure_end) if isinstance(closure_end, str) else closure_end
                        if c_start <= end_date and c_end >= start_date:
                                all_closures.append(closure)
                    except (ValueError, TypeError):
                        pass
        return all_closures

    async def get_excluded_days_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get detailed exclusion data."""
        # 1. Get holidays
        years = set()
        years.add(start_date.year)
        years.add(end_date.year)
        
        holidays = []
        for year in years:
            h_list = await self.get_holidays(year, start_date, end_date)
            holidays.extend(h_list)

        holiday_map = {}
        for h in holidays:
            # Handle potential string dates if client returns strings
            h_date_raw = h.get("date")
            h_date = h_date_raw
            if isinstance(h_date_raw, str):
                try:
                    h_date = date.fromisoformat(h_date_raw)
                except ValueError:
                    pass
            
            if h_date:
                holiday_map[h_date.isoformat()] = h.get("name", "Festività")

        # 2. Closures
        closures = await self.get_company_closures(start_date, end_date)
        closure_map = {}
        closure_dates = set()
        
        for closure in closures:
            if closure.get("closure_type") == "total":
                closure_start = closure.get("start_date")
                closure_end = closure.get("end_date")
                closure_name = closure.get("name", "Chiusura Aziendale")
                if closure_start and closure_end:
                    try:
                        c_start = date.fromisoformat(closure_start) if isinstance(closure_start, str) else closure_start
                        c_end = date.fromisoformat(closure_end) if isinstance(closure_end, str) else closure_end
                        current_closure = c_start
                        while current_closure <= c_end:
                            iso = current_closure.isoformat()
                            closure_dates.add(iso)
                            closure_map[iso] = {
                                "name": closure_name,
                                "consumes_balance": closure.get("consumes_leave_balance", False),
                                "is_paid": closure.get("is_paid", True),
                                "affected_departments": closure.get("affected_departments")
                            }
                            current_closure += timedelta(days=1)
                    except (ValueError, TypeError):
                        pass

        # 3. Work week config
        working_days_limit_val = await self.get_system_config("work_week_days", 5)
        try:
            working_days_limit = int(working_days_limit_val)
        except (ValueError, TypeError):
            working_days_limit = 5

        # 4. Weekends logic and assembly
        excluded_dates_set = set()
        details = {}
        
        day_names = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        
        current = start_date
        working_days_count = 0
        
        while current <= end_date:
            iso = current.isoformat()
            weekday = current.weekday()
            
            is_excluded = False
            reason = ""
            name = ""
            
            if weekday >= working_days_limit:
                 is_excluded = True
                 reason = "weekend"
                 name = day_names[weekday]
            elif iso in holiday_map:
                 is_excluded = True
                 reason = "holiday"
                 name = holiday_map[iso]
            elif iso in closure_map:
                 is_excluded = True
                 reason = "closure"
                 name = closure_map[iso]["name"]
            
            if is_excluded:
                excluded_dates_set.add(iso)
                details[iso] = {
                    "date": current,
                    "reason": reason,
                    "name": name,
                    "info": closure_map.get(iso) if reason == "closure" else None
                }
            else:
                working_days_count += 1
            
            current += timedelta(days=1)

        return {
            "excluded_dates": excluded_dates_set,
            "details": details,
            "working_days_count": working_days_count,
            "working_days_limit": working_days_limit
        }

    async def calculate_working_days(
        self, 
        start_date: date, 
        end_date: date, 
        start_half: bool = False, 
        end_half: bool = False
    ) -> Decimal:
        """Calculate number of working days."""
        data = await self.get_excluded_days_data(start_date, end_date)
        working_days = Decimal(data["working_days_count"])
        
        if start_half and working_days > 0:
            working_days -= Decimal("0.5")
        if end_half and working_days > 0:
            working_days -= Decimal("0.5")
            
        return working_days

    async def get_excluded_list(self, start_date: date, end_date: date) -> dict:
        """Format for UI response."""
        data = await self.get_excluded_days_data(start_date, end_date)
        details = data["details"]
        
        # Convert dict to sorted list
        sorted_keys = sorted(details.keys())
        excluded_list = []
        for k in sorted_keys:
            val = details[k]
            item = {
                "date": val["date"],
                "reason": val["reason"],
                "name": val["name"]
            }
            if val["info"]:
                item.update(val["info"])
            excluded_list.append(item)
            
        return {
            "start_date": start_date,
            "end_date": end_date,
            "working_days": data["working_days_count"],
            "excluded_days": excluded_list
        }
