from pydantic import BaseModel, Field
from typing import List, Optional

class HospitalInfo(BaseModel):
    """Structured hospital information model"""
    name: str = Field(description="Hospital name")
    address: str = Field(description="Hospital address")
    distance_km: float = Field(description="Distance from query location in kilometers")
    contact_number: Optional[str] = Field(default=None, description="Hospital contact/phone number")
    rating: Optional[float] = Field(default=None, description="Hospital rating out of 5")
    location_coordinates: Optional[dict] = Field(default=None, description="Latitude and longitude coordinates")
    place_id: Optional[str] = Field(default=None, description="Google Places ID for additional details")

class HospitalSearchResult(BaseModel):
    """Container for hospital search results"""
    query_location: str = Field(description="The location that was searched")
    hospitals: List[HospitalInfo] = Field(description="List of nearby hospitals")
    total_found: int = Field(description="Total number of hospitals found")
    search_radius_km: float = Field(description="Search radius used in kilometers")
    
    class Config:
        json_encoders = {
            float: lambda v: round(v, 2)
        }

class PoliceStationInfo(BaseModel):
    """Structured police station information model"""
    name: str = Field(description="Police station name")
    full_address: str = Field(description="Complete police station address")
    distance_km: float = Field(description="Distance from query location in kilometers")
    contact_number: Optional[str] = Field(default=None, description="Police station contact/phone number")
    rating: Optional[float] = Field(default=None, description="Police station rating out of 5")
    location_coordinates: Optional[dict] = Field(default=None, description="Latitude and longitude coordinates")
    place_id: Optional[str] = Field(default=None, description="Google Places ID for additional details")

class PoliceStationSearchResult(BaseModel):
    """Container for police station search results"""
    query_location: str = Field(description="The location that was searched")
    police_stations: List[PoliceStationInfo] = Field(description="List of nearby police stations")
    total_found: int = Field(description="Total number of police stations found")
    search_radius_km: float = Field(description="Search radius used in kilometers")
    
    class Config:
        json_encoders = {
            float: lambda v: round(v, 2)
        }