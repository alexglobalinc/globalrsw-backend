from pydantic import BaseModel
from typing import Optional, List

class PropertyFilter(BaseModel):
    state: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    zip_codes: Optional[List[str]] = None  # Changed to handle multiple zipcodes
    property_type: Optional[str] = None
    page: int = 1
    page_size: int = 10
    sort_by: Optional[str] = None
    sort_direction: Optional[str] = None


class ExportRequest(BaseModel):
    format: str
    selected_ids: Optional[List[str]] = None
    filters: Optional[PropertyFilter] = None