import os
import requests
from dotenv import load_dotenv
import math

load_dotenv()

class LocationServices:
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_PLACES_API_KEY') or os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.google_api_key:
            raise ValueError("Google Maps API key not found in environment variables")
    
    def get_coordinates(self, location):
        geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': location,
            'key': self.google_api_key
        }
        
        try:
            response = requests.get(geocoding_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location_data = data['results'][0]['geometry']['location']
                return location_data['lat'], location_data['lng']
            else:
                return None, None
        except Exception as e:
            print(f"Error getting coordinates: {e}")
            return None, None
    
    def find_nearby_places(self, location, place_type="hospital", radius=5000):
        lat, lng = self.get_coordinates(location)
        if lat is None or lng is None:
            return []
        
        places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            'location': f"{lat},{lng}",
            'radius': radius,
            'type': place_type,
            'key': self.google_api_key
        }
        
        try:
            response = requests.get(places_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            places = []
            if data['status'] == 'OK':
                for place in data['results']:
                    place_lat = place['geometry']['location']['lat']
                    place_lng = place['geometry']['location']['lng']
                    distance = self._calculate_distance(lat, lng, place_lat, place_lng)
                    
                    place_info = {
                        'name': place.get('name', 'Unknown'),
                        'address': place.get('vicinity', 'Address not available'),
                        'distance_km': round(distance, 2),
                        'rating': place.get('rating'),
                        'place_id': place.get('place_id'),
                        'location': {
                            'lat': place_lat,
                            'lng': place_lng
                        }
                    }
                    places.append(place_info)
                
                places.sort(key=lambda x: x['distance_km'])
            
            return places
        except Exception as e:
            print(f"Error finding nearby places: {e}")
            return []
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        R = 6371
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance = R * c
        return distance
    
    def get_place_details(self, place_id):
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            'place_id': place_id,
            'fields': 'name,formatted_address,formatted_phone_number,rating,geometry',
            'key': self.google_api_key
        }
        
        try:
            response = requests.get(details_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK':
                return data['result']
            else:
                return None
        except Exception as e:
            print(f"Error getting place details: {e}")
            return None
    
    def find_nearby_hospitals_structured(self, location, radius=5000):
        hospitals = self.find_nearby_places(location, "hospital", radius)
       
        hospitals = hospitals[:20] # hospitals[:8]
        
        structured_hospitals = []
        for hospital in hospitals:
            hospital_info = {
                'name': hospital['name'],
                'address': hospital['address'],
                'distance_km': hospital['distance_km'],
                'rating': hospital.get('rating'),
                'location_coordinates': hospital['location'],
                'place_id': hospital.get('place_id')
            }
            
            if hospital.get('place_id'):
                details = self.get_place_details(hospital['place_id'])
                if details:
                    hospital_info['contact_number'] = details.get('formatted_phone_number')
                    if 'formatted_address' in details:
                        hospital_info['address'] = details['formatted_address']
            
            structured_hospitals.append(hospital_info)
        
        return {
            'query_location': location,
            'hospitals': structured_hospitals,
            'total_found': len(structured_hospitals),
            'search_radius_km': radius / 1000
        }