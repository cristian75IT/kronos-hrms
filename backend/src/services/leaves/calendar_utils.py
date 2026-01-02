from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List, Set, Union

from src.shared.clients import ConfigClient, CalendarClient

class CalendarUtils:
    """Utilities for calendar calculations (working days, holidays, closures).
    
    Uses the Calendar microservice as the single source of truth.
    ConfigClient is only used for system configuration (work_week_days, etc).
    """

    def __init__(self, config_client: ConfigClient = None, calendar_client: CalendarClient = None):
        self.config_client = config_client or ConfigClient()
        self.calendar_client = calendar_client or CalendarClient()

    async def get_system_config(self, key: str, default: Any = None) -> Any:
        return await self.config_client.get_sys_config(key, default)

    async def get_holidays(self, year: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[dict]:
        """Get holidays for a specific year from Calendar Service."""
        try:
            return await self.calendar_client.get_holidays(year, start_date, end_date)
        except Exception as e:
            print(f"CalendarClient get_holidays failed: {e}")
            return []

    async def get_company_closures(self, start_date: date, end_date: date) -> List[dict]:
        """Get company closures from Calendar Service."""
        years = set([start_date.year, end_date.year])
        
        all_closures = []
        for year in years:
            try:
                closures = await self.calendar_client.get_closures(year)
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
            except Exception as e:
                print(f"CalendarClient get_closures failed for year {year}: {e}")
        
        return all_closures

    async def get_excluded_days_data(self, start_date: date, end_date: date, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get detailed exclusion data using the Calendar microservice."""
        location_id = None
        if user_id:
            try:
                from src.shared.clients import AuthClient
                auth_client = AuthClient()
                user_info = await auth_client.get_user_info(user_id)
                if user_info:
                    loc_id = user_info.get("location_id")
                    if loc_id:
                        location_id = UUID(loc_id) if isinstance(loc_id, str) else loc_id
            except Exception:
                pass

        try:
            # Use Calendar microservice as the source of truth
            range_view = await self.calendar_client.get_calendar_range(
                start_date=start_date,
                end_date=end_date,
                location_id=location_id
            )
            
            if range_view:
                excluded_dates_set = set()
                details = {}
                working_days_count = 0
                
                for day in range_view.get("days", []):
                    d_str = day.get("date")
                    d_date = date.fromisoformat(d_str) if isinstance(d_str, str) else d_str
                    iso = d_date.isoformat()
                    
                    if not day.get("is_working_day"):
                        excluded_dates_set.add(iso)
                        
                        # Identify the primary reason
                        items = day.get("items", [])
                        reason = "weekend"
                        name = ""
                        info = None
                        
                        holiday_item = next((i for i in items if i.get("item_type") == "holiday"), None)
                        closure_item = next((i for i in items if i.get("item_type") == "closure"), None)
                        
                        if holiday_item:
                            reason = "holiday"
                            name = holiday_item.get("title")
                        elif closure_item:
                            reason = "closure"
                            name = closure_item.get("title")
                            info = {
                                "name": name,
                                "is_paid": closure_item.get("metadata", {}).get("is_paid", True),
                                "consumes_balance": closure_item.get("metadata", {}).get("consumes_leave_balance", False)
                            }
                        else:
                            # If no holiday/closure but not working, it's weekend or non-working exception
                            day_names = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
                            name = day_names[d_date.weekday()]
                            
                        details[iso] = {
                            "date": d_date,
                            "reason": reason,
                            "name": name,
                            "info": info
                        }
                    else:
                        working_days_count += 1
                        
                return {
                    "excluded_dates": excluded_dates_set,
                    "details": details,
                    "working_days_count": working_days_count,
                    "working_days_limit": 5  # Default
                }
        except Exception as e:
            print(f"Calendar service get_calendar_range failed: {e}")
        
        # Fallback: compute locally using holidays and closures from Calendar Service
        years = set([start_date.year, end_date.year])
        holiday_map = {}
        for year in years:
            h_list = await self.get_holidays(year, start_date, end_date)
            for h in h_list:
                h_date_raw = h.get("date")
                h_date = date.fromisoformat(h_date_raw) if isinstance(h_date_raw, str) else h_date_raw
                if h_date:
                    holiday_map[h_date.isoformat()] = h.get("name", "Festività")

        closures = await self.get_company_closures(start_date, end_date)
        closure_map = {}
        for closure in closures:
            if closure.get("closure_type") == "total":
                c_start = date.fromisoformat(closure["start_date"]) if isinstance(closure["start_date"], str) else closure["start_date"]
                c_end = date.fromisoformat(closure["end_date"]) if isinstance(closure["end_date"], str) else closure["end_date"]
                current = c_start
                while current <= c_end:
                    iso = current.isoformat()
                    closure_map[iso] = {
                        "name": closure.get("name", "Chiusura Aziendale"),
                        "consumes_balance": closure.get("consumes_leave_balance", False),
                        "is_paid": closure.get("is_paid", True)
                    }
                    current += timedelta(days=1)

        working_days_limit_val = await self.get_system_config("work_week_days", 5)
        working_days_limit = int(working_days_limit_val)

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
            
            if iso in holiday_map:
                 is_excluded = True
                 reason = "holiday"
                 name = holiday_map[iso]
            elif iso in closure_map:
                 is_excluded = True
                 reason = "closure"
                 name = closure_map[iso]["name"]
            elif weekday >= working_days_limit:
                 is_excluded = True
                 reason = "weekend"
                 name = day_names[weekday]
            
            if is_excluded:
                excluded_dates_set.add(iso)
                details[iso] = {
                    "date": current, "reason": reason, "name": name,
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
        end_half: bool = False,
        user_id: Optional[UUID] = None
    ) -> Decimal:
        """Calculate number of working days."""
        data = await self.get_excluded_days_data(start_date, end_date, user_id=user_id)
        working_days = Decimal(data["working_days_count"])
        
        if start_half and working_days > 0:
            working_days -= Decimal("0.5")
        if end_half and working_days > 0:
            working_days -= Decimal("0.5")
            
        return working_days

    async def get_excluded_list(self, start_date: date, end_date: date, user_id: Optional[UUID] = None) -> dict:
        """Format for UI response."""
        data = await self.get_excluded_days_data(start_date, end_date, user_id=user_id)
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
