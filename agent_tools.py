from langchain.tools import Tool
from location_services import LocationServices
from typing import List, Dict
from models import HospitalSearchResult
import json


from models import HospitalSearchResult

class AgentTools:
    def __init__(self):
        self.location_service = LocationServices()
    
    def find_hospitals_structured(self, location: str) -> str:
        """Find nearby hospitals with structured output"""
        hospital_result = self.location_service.find_nearby_hospitals_structured(location)
        
        if hospital_result['total_found'] == 0:
            return f"I'm having trouble finding hospitals near {location} right now 💜 Please double-check the location name and try again, or I can help you with emergency numbers: 102 (Ambulance)."
        
        result = f"🏥 **Hospitals near {hospital_result['query_location']}:**\n\n"
        result += f"📊 **Found {hospital_result['total_found']} hospitals within {hospital_result['search_radius_km']} km**\n\n"
        
        for i, hospital in enumerate(hospital_result['hospitals'], 1):
            result += f"**{i}. {hospital['name']}**\n"
            result += f"   📍 **Address:** {hospital['address']}\n"
            result += f"   📏 **Distance:** {hospital['distance_km']} km away\n"
            
            if hospital.get('contact_number'):
                result += f"   📞 **Contact:** {hospital['contact_number']}\n"
            else:
                result += f"   📞 **Contact:** Not available\n"
                
            if hospital.get('rating'):
                result += f"   ⭐ **Rating:** {hospital['rating']}/5\n"
            
            if hospital.get('location_coordinates'):
                result += f"   🗺️ **Coordinates:** {hospital['location_coordinates']['lat']}, {hospital['location_coordinates']['lng']}\n"
            
            result += "\n"
        
        result += "\n🚨 **Emergency Number:** 102 (Ambulance)\n"
        result += "💡 **Tip:** Call ahead to check availability and services."
        
        return result
    
    def get_hospitals_json(self, location: str) -> str:
        """Get hospitals data as JSON for API responses"""
        hospital_result = self.location_service.find_nearby_hospitals_structured(location)
        return json.dumps(hospital_result, indent=2)
    
    def find_police_stations(self, location: str) -> str:
        """Find nearby police stations"""
        stations = self.location_service.find_nearby_places(location, 'police')
        
        if stations and 'error' in stations[0]:
            return f"I'm having trouble finding police stations right now 💜 Please try again in a moment, or call emergency: 100 (Police)"
        
        if not stations:
            return f"I'm having trouble finding police stations near {location} right now 💜 Please double-check the location name and try again, or call emergency: 100 (Police)"
        
        result = f"🚔 **Police Stations near {location}:**\n\n"
        for i, station in enumerate(stations, 1):
            result += f"**{i}. {station['name']}**\n"
            result += f"   📍 **Address:** {station['address']}\n"
            if station.get('rating'):
                result += f"   ⭐ **Rating:** {station['rating']}/5\n"
            result += f"   📏 **Distance:** {station['distance_km']} km\n"
            result += "\n"
        
        result += "\n🚨 **Emergency Number:** 100 (Police)\n"
        result += "💡 **Tip:** Save these numbers in your phone for quick access."
        
        return result
    
    def find_emergency_services(self, location: str) -> str:
        """Find all emergency services"""
        hospitals = self.location_service.find_nearby_places(location, 'hospital')[:3]
        police = self.location_service.find_nearby_places(location, 'police')[:3]
        
        result = f"🚨 **Emergency Services near {location}:**\n\n"
        
        if hospitals and 'error' not in hospitals[0]:
            result += "🏥 **Nearest Hospitals:**\n"
            for hospital in hospitals:
                result += f"• **{hospital['name']}** - {hospital['distance_km']} km\n"
                result += f"  📍 {hospital['address']}\n"
            result += "\n"
        
        if police and 'error' not in police[0]:
            result += "🚔 **Nearest Police Stations:**\n"
            for station in police:
                result += f"• **{station['name']}** - {station['distance_km']} km\n"
                result += f"  📍 {station['address']}\n"
            result += "\n"
        
        result += "📞 **Emergency Numbers:**\n"
        result += "• 🚨 **Police:** 100\n"
        result += "• 🏥 **Ambulance:** 102\n"
        result += "• 🔥 **Fire:** 101\n"
        result += "• 🆘 **Women Helpline:** 1091\n"
        result += "• 📱 **Emergency:** 112 (All services)\n\n"
        result += "💡 **Safety Tip:** Share your location with trusted contacts when in emergency."
        
        return result
    
    def find_safe_places(self, location: str) -> str:
        """Find safe places like malls, hotels, etc."""
        # Search for multiple types of safe places
        malls = self.location_service.find_nearby_places(location, 'shopping_mall')[:3]
        hotels = self.location_service.find_nearby_places(location, 'lodging')[:3]
        restaurants = self.location_service.find_nearby_places(location, 'restaurant')[:3]
        
        result = f"🛡️ **Safe Places near {location}:**\n\n"
        
        if malls and 'error' not in malls[0]:
            result += "🏬 **Shopping Malls (Well-lit, Security):**\n"
            for mall in malls:
                result += f"• **{mall['name']}** - {mall['distance_km']} km\n"
            result += "\n"
        
        if hotels and 'error' not in hotels[0]:
            result += "🏨 **Hotels (24/7 Reception):**\n"
            for hotel in hotels:
                result += f"• **{hotel['name']}** - {hotel['distance_km']} km\n"
            result += "\n"
        
        if restaurants and 'error' not in restaurants[0]:
            result += "🍽️ **Restaurants (Public Places):**\n"
            for restaurant in restaurants:
                result += f"• **{restaurant['name']}** - {restaurant['distance_km']} km\n"
            result += "\n"
        
        result += "💡 **Safety Tips:**\n"
        result += "• Choose well-lit, crowded places\n"
        result += "• Look for places with security cameras\n"
        result += "• Avoid isolated areas, especially at night\n"
        result += "• Trust your instincts - if something feels wrong, leave"
        
        return result
    
    def get_tools(self) -> List[Tool]:
        """Get all available tools for the agent"""
        return [
            Tool(
                name="find_hospitals",
                description="Find nearby hospitals. Use this when someone asks about hospitals, medical facilities, or emergency medical care near a location.",
                func=self.find_hospitals_structured  # Updated to use structured version
            ),
            Tool(
                name="get_hospitals_json",
                description="Get hospital data in JSON format for structured responses.",
                func=self.get_hospitals_json
            ),
            Tool(
                name="find_police_stations",
                description="Find nearby police stations and law enforcement facilities. Input should be a location name, address, or city name.",
                func=self.find_police_stations
            ),
            Tool(
                name="find_emergency_services",
                description="Find all emergency services including hospitals, police stations, and emergency contact numbers. Input should be a location name, address, or city name.",
                func=self.find_emergency_services
            ),
            Tool(
                name="find_safe_places",
                description="Find safe places like malls, hotels, restaurants where someone can seek help or feel secure. Input should be a location name, address, or city name.",
                func=self.find_safe_places
            )
        ]