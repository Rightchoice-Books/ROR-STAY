import googlemaps
from typing import Optional, List, Dict, Any
from models import Coordinates, Address
from config import get_settings
from fastapi import HTTPException
import logging
from geopy.distance import geodesic

logger = logging.getLogger(__name__)
settings = get_settings()

class GoogleMapsService:
    def __init__(self):
        if not settings.google_maps_api_key:
            logger.warning("Google Maps API key not configured. Maps functionality will be limited.")
            self.client = None
        else:
            try:
                self.client = googlemaps.Client(key=settings.google_maps_api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Google Maps client: {e}")
                self.client = None
        
        self.geocoding_cache = {}
    
    def _is_configured(self) -> bool:
        """Check if Google Maps service is properly configured"""
        return self.client is not None
    
    async def geocode_address(self, address: str) -> Optional[Coordinates]:
        """
        Convert address to coordinates using Google Geocoding API
        
        Args:
            address: Address string to geocode
            
        Returns:
            Coordinates object or None if geocoding fails
        """
        if not self._is_configured():
            logger.warning("Google Maps API not configured. Cannot geocode address.")
            return None
        
        # Check cache first
        if address in self.geocoding_cache:
            logger.info(f"Using cached geocoding result for: {address}")
            return self.geocoding_cache[address]
        
        try:
            geocode_result = self.client.geocode(address)
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                coordinates = Coordinates(
                    latitude=location['lat'],
                    longitude=location['lng']
                )
                
                # Cache the result
                self.geocoding_cache[address] = coordinates
                logger.info(f"Successfully geocoded address: {address}")
                return coordinates
            else:
                logger.warning(f"No geocoding results for address: {address}")
                return None
                
        except Exception as e:
            logger.error(f"Geocoding failed for address '{address}': {e}")
            raise HTTPException(status_code=500, detail=f"Geocoding failed: {str(e)}")
    
    async def reverse_geocode(self, coordinates: Coordinates) -> Optional[Address]:
        """
        Convert coordinates to address using Google Reverse Geocoding API
        
        Args:
            coordinates: Coordinates object
            
        Returns:
            Address object or None if reverse geocoding fails
        """
        if not self._is_configured():
            logger.warning("Google Maps API not configured. Cannot reverse geocode coordinates.")
            return None
        
        try:
            reverse_geocode_result = self.client.reverse_geocode(
                (coordinates.latitude, coordinates.longitude)
            )
            
            if reverse_geocode_result:
                result = reverse_geocode_result[0]
                components = result['address_components']
                
                address_data = {
                    'street': '',
                    'city': '',
                    'state': '',
                    'zip_code': '',
                    'country': '',
                    'full_address': result['formatted_address']
                }
                
                # Parse address components
                for component in components:
                    types = component['types']
                    if 'street_number' in types:
                        address_data['street'] = component['long_name'] + ' '
                    elif 'route' in types:
                        address_data['street'] += component['long_name']
                    elif 'locality' in types:
                        address_data['city'] = component['long_name']
                    elif 'administrative_area_level_1' in types:
                        address_data['state'] = component['short_name']
                    elif 'postal_code' in types:
                        address_data['zip_code'] = component['long_name']
                    elif 'country' in types:
                        address_data['country'] = component['long_name']
                
                # Clean up street address
                address_data['street'] = address_data['street'].strip()
                
                logger.info(f"Successfully reverse geocoded coordinates: {coordinates.latitude}, {coordinates.longitude}")
                return Address(**address_data)
            else:
                logger.warning(f"No reverse geocoding results for coordinates: {coordinates.latitude}, {coordinates.longitude}")
                return None
                
        except Exception as e:
            logger.error(f"Reverse geocoding failed for coordinates {coordinates.latitude}, {coordinates.longitude}: {e}")
            raise HTTPException(status_code=500, detail=f"Reverse geocoding failed: {str(e)}")
    
    async def calculate_distance(self, origin: Coordinates, destination: Coordinates) -> float:
        """
        Calculate distance between two coordinates in miles
        
        Args:
            origin: Starting coordinates
            destination: Ending coordinates
            
        Returns:
            Distance in miles
        """
        try:
            distance = geodesic(
                (origin.latitude, origin.longitude),
                (destination.latitude, destination.longitude)
            ).miles
            
            logger.info(f"Calculated distance: {distance:.2f} miles")
            return distance
            
        except Exception as e:
            logger.error(f"Distance calculation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Distance calculation failed: {str(e)}")
    
    async def get_nearby_places(
        self, 
        coordinates: Coordinates, 
        place_type: str = "school", 
        radius: int = 5000
    ) -> List[Dict[str, Any]]:
        """
        Get nearby places of interest using Google Places API
        
        Args:
            coordinates: Center coordinates for search
            place_type: Type of place to search for (school, hospital, restaurant, etc.)
            radius: Search radius in meters (max 50000)
            
        Returns:
            List of places with their details
        """
        if not self._is_configured():
            logger.warning("Google Maps API not configured. Cannot search for nearby places.")
            return []
        
        try:
            places_result = self.client.places_nearby(
                location=(coordinates.latitude, coordinates.longitude),
                radius=min(radius, 50000),  # Google API limit
                type=place_type
            )
            
            places = []
            for place in places_result.get('results', []):
                place_info = {
                    'name': place.get('name', ''),
                    'place_id': place.get('place_id', ''),
                    'types': place.get('types', []),
                    'rating': place.get('rating'),
                    'user_ratings_total': place.get('user_ratings_total'),
                    'vicinity': place.get('vicinity', ''),
                    'coordinates': {
                        'latitude': place['geometry']['location']['lat'],
                        'longitude': place['geometry']['location']['lng']
                    }
                }
                places.append(place_info)
            
            logger.info(f"Found {len(places)} nearby {place_type}s")
            return places
            
        except Exception as e:
            logger.error(f"Nearby places search failed: {e}")
            raise HTTPException(status_code=500, detail=f"Places search failed: {str(e)}")
    
    async def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific place
        
        Args:
            place_id: Google Places ID
            
        Returns:
            Place details or None if not found
        """
        if not self._is_configured():
            logger.warning("Google Maps API not configured. Cannot get place details.")
            return None
        
        try:
            place_details = self.client.place(place_id=place_id)
            
            if place_details and 'result' in place_details:
                result = place_details['result']
                
                details = {
                    'name': result.get('name', ''),
                    'place_id': result.get('place_id', ''),
                    'formatted_address': result.get('formatted_address', ''),
                    'formatted_phone_number': result.get('formatted_phone_number'),
                    'website': result.get('website'),
                    'rating': result.get('rating'),
                    'user_ratings_total': result.get('user_ratings_total'),
                    'types': result.get('types', []),
                    'opening_hours': result.get('opening_hours', {}).get('weekday_text', []),
                    'coordinates': {
                        'latitude': result['geometry']['location']['lat'],
                        'longitude': result['geometry']['location']['lng']
                    } if 'geometry' in result else None
                }
                
                logger.info(f"Retrieved details for place: {details['name']}")
                return details
            else:
                logger.warning(f"No details found for place ID: {place_id}")
                return None
                
        except Exception as e:
            logger.error(f"Place details retrieval failed for place_id {place_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Place details retrieval failed: {str(e)}")
    
    async def get_directions(
        self, 
        origin: Coordinates, 
        destination: Coordinates, 
        mode: str = "driving"
    ) -> Optional[Dict[str, Any]]:
        """
        Get directions between two points
        
        Args:
            origin: Starting coordinates
            destination: Ending coordinates
            mode: Transportation mode (driving, walking, transit, bicycling)
            
        Returns:
            Directions information or None if not found
        """
        if not self._is_configured():
            logger.warning("Google Maps API not configured. Cannot get directions.")
            return None
        
        try:
            directions_result = self.client.directions(
                origin=(origin.latitude, origin.longitude),
                destination=(destination.latitude, destination.longitude),
                mode=mode
            )
            
            if directions_result:
                route = directions_result[0]  # First route
                leg = route['legs'][0]  # First leg
                
                directions = {
                    'distance': leg['distance']['text'],
                    'duration': leg['duration']['text'],
                    'start_address': leg['start_address'],
                    'end_address': leg['end_address'],
                    'steps': [
                        {
                            'instruction': step['html_instructions'],
                            'distance': step['distance']['text'],
                            'duration': step['duration']['text']
                        }
                        for step in leg['steps']
                    ]
                }
                
                logger.info(f"Retrieved directions: {directions['distance']}, {directions['duration']}")
                return directions
            else:
                logger.warning("No directions found for the given coordinates")
                return None
                
        except Exception as e:
            logger.error(f"Directions retrieval failed: {e}")
            raise HTTPException(status_code=500, detail=f"Directions retrieval failed: {str(e)}")
    
    def generate_static_map_url(
        self, 
        center: Coordinates, 
        zoom: int = 15, 
        size: str = "400x400",
        markers: Optional[List[Coordinates]] = None
    ) -> Optional[str]:
        """
        Generate URL for static map image
        
        Args:
            center: Center coordinates for the map
            zoom: Zoom level (1-20)
            size: Image size in format "widthxheight"
            markers: Optional list of marker coordinates
            
        Returns:
            Static map URL or None if not configured
        """
        if not self._is_configured():
            logger.warning("Google Maps API not configured. Cannot generate static map URL.")
            return None
        
        try:
            base_url = "https://maps.googleapis.com/maps/api/staticmap"
            params = {
                "center": f"{center.latitude},{center.longitude}",
                "zoom": zoom,
                "size": size,
                "key": settings.google_maps_api_key,
                "maptype": "roadmap",
                "format": "png"
            }
            
            # Add markers if provided
            if markers:
                marker_strings = []
                for i, marker in enumerate(markers):
                    marker_strings.append(f"color:red|label:{i+1}|{marker.latitude},{marker.longitude}")
                params["markers"] = "|".join(marker_strings)
            
            # Build URL
            param_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{base_url}?{param_string}"
            
            logger.info("Generated static map URL")
            return url
            
        except Exception as e:
            logger.error(f"Static map URL generation failed: {e}")
            return None

# Create a singleton instance
maps_service = GoogleMapsService()

# Dependency for FastAPI
def get_maps_service() -> GoogleMapsService:
    return maps_service