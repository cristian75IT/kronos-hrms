import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    from src.services.calendar.routers import admin
    print("Admin router imported successfully")
except Exception as e:
    print(f"Error importing admin router: {e}")
    import traceback
    traceback.print_exc()
