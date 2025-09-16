from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from models import Coordinates, APIResponse
from maps_service import get_maps_service, GoogleMapsService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/maps", tags=["maps"])

@router.post("/geocode", response_model=dict)
async def geocode_address(
    address: str,
    maps_service: GoogleMapsService = Depends(get_maps_service)
):
    """Convert address to coordinates"""
    try:
        coordinates = await maps_service.geocode_address(address)
        
        if not coordinates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found or could not be geocoded"
            )
        
        return {
            "success": True,
            "address": address,
            "coordinates": coordinates.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error geocoding address '{address}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Geocoding failed"
        )

@router.post("/reverse-geocode", response_model=dict)
async def reverse_geocode_coordinates(
    coordinates: Coordinates,
    maps_service: GoogleMapsService = Depends(get_maps_service)
):
    """Convert coordinates to address"""
    try:
        address = await maps_service.reverse_geocode(coordinates)
        
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found for the given coordinates"
            )
        
        return {
            "success": True,
            "coordinates": coordinates.dict(),
            "address": address.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reverse geocoding coordinates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Reverse geocoding failed"
        )

@router.get("/distance", response_model=dict)
async def calculate_distance(
    origin_lat: float = Query(..., description="Origin latitude"),
    origin_lng: float = Query(..., description="Origin longitude"),
    dest_lat: float = Query(..., description="Destination latitude"),
    dest_lng: float = Query(..., description="Destination longitude"),
    maps_service: GoogleMapsService = Depends(get_maps_service)
):
    """Calculate distance between two coordinates"""
    try:
        origin = Coordinates(latitude=origin_lat, longitude=origin_lng)
        destination = Coordinates(latitude=dest_lat, longitude=dest_lng)
        
        distance_miles = await maps_service.calculate_distance(origin, destination)
        
        return {
            "success": True,
            "origin": origin.dict(),
            "destination": destination.dict(),
            "distance_miles": round(distance_miles, 2),
            "distance_km": round(distance_miles * 1.60934, 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating distance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Distance calculation failed"
        )

@router.get("/nearby-places", response_model=List[dict])
async def get_nearby_places(
    latitude: float = Query(..., description="Center latitude"),
    longitude: float = Query(..., description="Center longitude"),
    place_type: str = Query("school", description="Type of place to search for"),
    radius: int = Query(5000, ge=100, le=50000, description="Search radius in meters"),
    maps_service: GoogleMapsService = Depends(get_maps_service)
):
    """Get nearby places of interest"""
    try:
        coordinates = Coordinates(latitude=latitude, longitude=longitude)
        places = await maps_service.get_nearby_places(coordinates, place_type, radius)
        
        return places
        
    except Exception as e:
        logger.error(f"Error finding nearby places: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find nearby places"
        )

@router.get("/place-details/{place_id}", response_model=dict)
async def get_place_details(
    place_id: str,
    maps_service: GoogleMapsService = Depends(get_maps_service)
):
    """Get detailed information about a specific place"""
    try:
        place_details = await maps_service.get_place_details(place_id)
        
        if not place_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Place not found"
            )
        
        return {
            "success": True,
            "place_details": place_details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving place details for {place_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve place details"
        )

@router.get("/directions", response_model=dict)
async def get_directions(
    origin_lat: float = Query(..., description="Origin latitude"),
    origin_lng: float = Query(..., description="Origin longitude"),
    dest_lat: float = Query(..., description="Destination latitude"),
    dest_lng: float = Query(..., description="Destination longitude"),
    mode: str = Query("driving", regex="^(driving|walking|transit|bicycling)$", description="Transportation mode"),
    maps_service: GoogleMapsService = Depends(get_maps_service)
):
    """Get directions between two points"""
    try:
        origin = Coordinates(latitude=origin_lat, longitude=origin_lng)
        destination = Coordinates(latitude=dest_lat, longitude=dest_lng)
        
        directions = await maps_service.get_directions(origin, destination, mode)
        
        if not directions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Directions not found for the given coordinates"
            )
        
        return {
            "success": True,
            "origin": origin.dict(),
            "destination": destination.dict(),
            "mode": mode,
            "directions": directions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving directions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve directions"
        )

@router.get("/static-map-url", response_model=dict)
async def generate_static_map_url(
    center_lat: float = Query(..., description="Center latitude"),
    center_lng: float = Query(..., description="Center longitude"),
    zoom: int = Query(15, ge=1, le=20, description="Zoom level"),
    size: str = Query("400x400", regex="^\\d+x\\d+$", description="Image size (widthxheight)"),
    marker_lat: Optional[float] = Query(None, description="Marker latitude"),
    marker_lng: Optional[float] = Query(None, description="Marker longitude"),
    maps_service: GoogleMapsService = Depends(get_maps_service)
):
    """Generate URL for static map image"""
    try:
        center = Coordinates(latitude=center_lat, longitude=center_lng)
        
        markers = None
        if marker_lat is not None and marker_lng is not None:
            markers = [Coordinates(latitude=marker_lat, longitude=marker_lng)]
        
        map_url = maps_service.generate_static_map_url(center, zoom, size, markers)
        
        if not map_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate static map URL"
            )
        
        return {
            "success": True,
            "map_url": map_url,
            "parameters": {
                "center": center.dict(),
                "zoom": zoom,
                "size": size,
                "markers": [m.dict() for m in markers] if markers else []
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating static map URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate static map URL"
        )

@router.get("/service-status", response_model=dict)
async def get_maps_service_status(
    maps_service: GoogleMapsService = Depends(get_maps_service)
):
    """Check if Google Maps service is configured and available"""
    try:
        is_configured = maps_service._is_configured()
        
        status_info = {
            "configured": is_configured,
            "message": "Google Maps service is available" if is_configured else "Google Maps service is not configured"
        }
        
        if is_configured:
            # Test with a simple geocoding request
            try:
                test_result = await maps_service.geocode_address("New York, NY")
                status_info["test_geocoding"] = test_result is not None
            except Exception:
                status_info["test_geocoding"] = False
                status_info["message"] = "Google Maps service configured but API calls are failing"
        
        return status_info
        
    except Exception as e:
        logger.error(f"Error checking maps service status: {e}")
        return {
            "configured": False,
            "message": "Error checking service status",
            "error": str(e)
        }