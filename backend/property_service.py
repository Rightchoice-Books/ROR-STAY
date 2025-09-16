from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from models import (
    Property, PropertyCreate, PropertyUpdate, PropertySearchFilters, 
    MapBounds, Coordinates, User, UserRole, generate_id, get_current_timestamp
)
from maps_service import GoogleMapsService
import logging
import math

logger = logging.getLogger(__name__)

class PropertyService:
    def __init__(self, db: AsyncIOMotorDatabase, maps_service: GoogleMapsService):
        self.db = db
        self.maps_service = maps_service
    
    async def create_property(self, property_data: PropertyCreate, current_user: User) -> Property:
        """
        Create a new property with automatic geocoding
        
        Args:
            property_data: Property data to create
            current_user: Current authenticated user
            
        Returns:
            Created property
        """
        try:
            # Check permissions - only admins and agents can create properties
            if current_user.role not in [UserRole.ADMIN, UserRole.AGENT]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins and agents can create properties"
                )
            
            # If coordinates not provided, geocode the address
            if not property_data.coordinates:
                coordinates = await self.maps_service.geocode_address(
                    property_data.address.full_address
                )
                if not coordinates:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, 
                        detail="Unable to geocode the provided address"
                    )
            else:
                coordinates = property_data.coordinates
            
            # Set agent_id to current user if they're an agent
            agent_id = property_data.agent_id
            if current_user.role == UserRole.AGENT:
                agent_id = current_user.id
            
            # Create property document
            current_time = get_current_timestamp()
            property_doc = {
                "id": generate_id(),
                "title": property_data.title,
                "property_type": property_data.property_type,
                "status": property_data.status,
                "price": property_data.price,
                "bedrooms": property_data.bedrooms,
                "bathrooms": property_data.bathrooms,
                "square_feet": property_data.square_feet,
                "description": property_data.description,
                "features": property_data.features,
                "images": property_data.images,
                "address": property_data.address.dict(),
                "coordinates": coordinates.dict(),
                "agent_id": agent_id,
                "created_at": current_time,
                "updated_at": current_time
            }
            
            # Insert into database
            result = await self.db.properties.insert_one(property_doc)
            
            if result.inserted_id:
                # Return the created property
                return Property(
                    **property_doc,
                    coordinates=coordinates
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create property"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating property: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create property"
            )
    
    async def get_property_by_id(self, property_id: str) -> Optional[Property]:
        """
        Get a property by its ID
        
        Args:
            property_id: Property ID
            
        Returns:
            Property object or None if not found
        """
        try:
            property_doc = await self.db.properties.find_one({"id": property_id})
            if property_doc:
                # Convert MongoDB document to Property model
                property_doc["id"] = str(property_doc.pop("_id", property_doc.get("id")))
                
                # Convert nested dictionaries back to models
                property_doc["coordinates"] = Coordinates(**property_doc["coordinates"])
                
                return Property(**property_doc)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching property by ID {property_id}: {e}")
            return None
    
    async def update_property(
        self, 
        property_id: str, 
        property_update: PropertyUpdate, 
        current_user: User
    ) -> Property:
        """
        Update an existing property
        
        Args:
            property_id: Property ID to update
            property_update: Updated property data
            current_user: Current authenticated user
            
        Returns:
            Updated property
        """
        try:
            # Get existing property
            existing_property = await self.get_property_by_id(property_id)
            if not existing_property:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Property not found"
                )
            
            # Check permissions
            if current_user.role == UserRole.AGENT and existing_property.agent_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update your own properties"
                )
            elif current_user.role not in [UserRole.ADMIN, UserRole.AGENT]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins and agents can update properties"
                )
            
            # Prepare update data
            update_data = {}
            update_fields = property_update.dict(exclude_unset=True)
            
            for field, value in update_fields.items():
                if value is not None:
                    if field == "address":
                        update_data["address"] = value.dict()
                        # If address changed, re-geocode
                        new_coordinates = await self.maps_service.geocode_address(value.full_address)
                        if new_coordinates:
                            update_data["coordinates"] = new_coordinates.dict()
                    elif field == "coordinates":
                        update_data["coordinates"] = value.dict()
                    else:
                        update_data[field] = value
            
            # Add updated timestamp
            update_data["updated_at"] = get_current_timestamp()
            
            # Update in database
            result = await self.db.properties.update_one(
                {"id": property_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No changes were made to the property"
                )
            
            # Return updated property
            updated_property = await self.get_property_by_id(property_id)
            if not updated_property:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve updated property"
                )
            
            return updated_property
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating property {property_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update property"
            )
    
    async def delete_property(self, property_id: str, current_user: User) -> bool:
        """
        Delete a property
        
        Args:
            property_id: Property ID to delete
            current_user: Current authenticated user
            
        Returns:
            True if deleted successfully
        """
        try:
            # Get existing property
            existing_property = await self.get_property_by_id(property_id)
            if not existing_property:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Property not found"
                )
            
            # Check permissions
            if current_user.role == UserRole.AGENT and existing_property.agent_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only delete your own properties"
                )
            elif current_user.role not in [UserRole.ADMIN, UserRole.AGENT]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins and agents can delete properties"
                )
            
            # Delete from database
            result = await self.db.properties.delete_one({"id": property_id})
            
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete property"
                )
            
            logger.info(f"Property {property_id} deleted by user {current_user.id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting property {property_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete property"
            )
    
    async def search_properties(self, filters: PropertySearchFilters) -> List[Property]:
        """
        Search properties based on filters
        
        Args:
            filters: Search filters
            
        Returns:
            List of matching properties
        """
        try:
            # Build MongoDB query
            query = {}
            
            # Apply map bounds filter if provided
            if filters.bounds:
                query["coordinates.latitude"] = {
                    "$gte": filters.bounds.southwest.latitude,
                    "$lte": filters.bounds.northeast.latitude
                }
                query["coordinates.longitude"] = {
                    "$gte": filters.bounds.southwest.longitude,
                    "$lte": filters.bounds.northeast.longitude
                }
            
            # Apply property type filter
            if filters.property_types:
                query["property_type"] = {"$in": filters.property_types}
            
            # Apply price filters
            if filters.min_price or filters.max_price:
                price_query = {}
                if filters.min_price:
                    price_query["$gte"] = filters.min_price
                if filters.max_price:
                    price_query["$lte"] = filters.max_price
                query["price"] = price_query
            
            # Apply bedroom filters
            if filters.min_bedrooms or filters.max_bedrooms:
                bedroom_query = {}
                if filters.min_bedrooms:
                    bedroom_query["$gte"] = filters.min_bedrooms
                if filters.max_bedrooms:
                    bedroom_query["$lte"] = filters.max_bedrooms
                query["bedrooms"] = bedroom_query
            
            # Apply bathroom filters
            if filters.min_bathrooms or filters.max_bathrooms:
                bathroom_query = {}
                if filters.min_bathrooms:
                    bathroom_query["$gte"] = filters.min_bathrooms
                if filters.max_bathrooms:
                    bathroom_query["$lte"] = filters.max_bathrooms
                query["bathrooms"] = bathroom_query
            
            # Apply square feet filters
            if filters.min_square_feet or filters.max_square_feet:
                sqft_query = {}
                if filters.min_square_feet:
                    sqft_query["$gte"] = filters.min_square_feet
                if filters.max_square_feet:
                    sqft_query["$lte"] = filters.max_square_feet
                query["square_feet"] = sqft_query
            
            # Apply status filter
            if filters.status:
                query["status"] = {"$in": filters.status}
            
            # Execute query
            properties = []
            cursor = self.db.properties.find(query).limit(1000)  # Reasonable limit
            
            async for property_doc in cursor:
                try:
                    # Convert MongoDB document to Property model
                    property_doc["id"] = str(property_doc.pop("_id", property_doc.get("id")))
                    property_doc["coordinates"] = Coordinates(**property_doc["coordinates"])
                    
                    properties.append(Property(**property_doc))
                except Exception as e:
                    logger.warning(f"Error processing property document: {e}")
                    continue
            
            logger.info(f"Found {len(properties)} properties matching filters")
            return properties
            
        except Exception as e:
            logger.error(f"Error searching properties: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search properties"
            )
    
    async def get_properties_by_agent(self, agent_id: str) -> List[Property]:
        """
        Get all properties for a specific agent
        
        Args:
            agent_id: Agent's user ID
            
        Returns:
            List of agent's properties
        """
        try:
            properties = []
            cursor = self.db.properties.find({"agent_id": agent_id})
            
            async for property_doc in cursor:
                try:
                    # Convert MongoDB document to Property model
                    property_doc["id"] = str(property_doc.pop("_id", property_doc.get("id")))
                    property_doc["coordinates"] = Coordinates(**property_doc["coordinates"])
                    
                    properties.append(Property(**property_doc))
                except Exception as e:
                    logger.warning(f"Error processing property document: {e}")
                    continue
            
            logger.info(f"Found {len(properties)} properties for agent {agent_id}")
            return properties
            
        except Exception as e:
            logger.error(f"Error fetching properties for agent {agent_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch agent properties"
            )
    
    async def get_nearby_properties(
        self, 
        coordinates: Coordinates, 
        radius_miles: float = 5.0,
        limit: int = 50
    ) -> List[Property]:
        """
        Get properties within a certain radius of coordinates
        
        Args:
            coordinates: Center coordinates
            radius_miles: Search radius in miles
            limit: Maximum number of properties to return
            
        Returns:
            List of nearby properties
        """
        try:
            # Calculate approximate bounding box (rough conversion)
            lat_delta = radius_miles / 69.0  # Approximate miles per degree latitude
            lng_delta = radius_miles / (69.0 * abs(math.cos(math.radians(coordinates.latitude))))
            
            bounds = MapBounds(
                southwest=Coordinates(
                    latitude=coordinates.latitude - lat_delta,
                    longitude=coordinates.longitude - lng_delta
                ),
                northeast=Coordinates(
                    latitude=coordinates.latitude + lat_delta,
                    longitude=coordinates.longitude + lng_delta
                )
            )
            
            # Use search with bounds
            filters = PropertySearchFilters(bounds=bounds)
            candidate_properties = await self.search_properties(filters)
            
            # Filter by exact radius using maps service
            nearby_properties = []
            for prop in candidate_properties:
                distance = await self.maps_service.calculate_distance(coordinates, prop.coordinates)
                if distance <= radius_miles:
                    nearby_properties.append(prop)
                
                if len(nearby_properties) >= limit:
                    break
            
            logger.info(f"Found {len(nearby_properties)} properties within {radius_miles} miles")
            return nearby_properties
            
        except Exception as e:
            logger.error(f"Error finding nearby properties: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to find nearby properties"
            )

# Dependency function
def get_property_service(
    db: AsyncIOMotorDatabase,
    maps_service: GoogleMapsService
) -> PropertyService:
    return PropertyService(db, maps_service)