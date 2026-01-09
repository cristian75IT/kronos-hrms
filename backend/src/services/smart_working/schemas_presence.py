from datetime import date
from pydantic import BaseModel

class SWPresenceCreate(BaseModel):
    date: date
    notes: str = "Lavoro in presenza"
