from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from datetime import datetime, timedelta
import re
from difflib import SequenceMatcher

from app.models.inventory import (
    InventoryItem, InventoryItemCreate, InventoryItemUpdate, 
    StockMovement, InventoryFilter, StockStatus
)

logger = logging.getLogger(__name__)

class InventoryService:
    
    async def get_inventory_items(
        self, 
        db: AsyncIOMotorDatabase, 
        filter_params: InventoryFilter
    ) -> List[InventoryItem]:
        """Get inventory items with filtering"""
        try:
            # Build MongoDB query
            query = {}
            
            if filter_params.category:
                query["category"] = {"$regex": filter_params.category, "$options": "i"}
            
            if filter_params.warehouse_id:
                query["warehouse_id"] = filter_params.warehouse_id
            
            if filter_params.supplier_id:
                query["supplier_id"] = filter_params.supplier_id
            
            if filter_params.status:
                query["status"] = filter_params.status
            
            if filter_params.low_stock_only:
                query["$expr"] = {"$lte": ["$current_stock", "$reorder_level"]}
            
            if filter_params.search:
                search_pattern = {"$regex": filter_params.search, "$options": "i"}
                query["$or"] = [
                    {"name": search_pattern},
                    {"sku": search_pattern},
                    {"description": search_pattern}
                ]
            
            # Execute query with pagination
            cursor = db.inventory.find(query).skip(filter_params.skip).limit(filter_params.limit)
            items_data = await cursor.to_list(length=filter_params.limit)
            
            # Convert to Pydantic models
            items = []
            for item_data in items_data:
                item_data["id"] = str(item_data["_id"])
                items.append(InventoryItem(**item_data))
            
            return items
            
        except Exception as e:
            logger.error(f"Error fetching inventory items: {str(e)}")
            raise
    
    async def get_inventory_item_by_sku(
        self, 
        db: AsyncIOMotorDatabase, 
        sku: str
    ) -> Optional[InventoryItem]:
        """Get inventory item by SKU"""
        try:
            item_data = await db.inventory.find_one({"sku": sku})
            if item_data:
                item_data["id"] = str(item_data["_id"])
                return InventoryItem(**item_data)
            return None
        except Exception as e:
            logger.error(f"Error fetching inventory item {sku}: {str(e)}")
            raise
    
    async def create_inventory_item(
        self, 
        db: AsyncIOMotorDatabase, 
        item_data: InventoryItemCreate
    ) -> InventoryItem:
        """Create new inventory item"""
        try:
            # Convert to dict and add metadata
            item_dict = item_data.dict()
            item_dict["created_at"] = datetime.utcnow()
            item_dict["updated_at"] = datetime.utcnow()
            
            # Determine initial status based on stock level
            if item_dict["current_stock"] == 0:
                item_dict["status"] = StockStatus.OUT_OF_STOCK
            elif item_dict["current_stock"] <= item_dict["reorder_level"]:
                item_dict["status"] = StockStatus.LOW_STOCK
            else:
                item_dict["status"] = StockStatus.IN_STOCK
            
            # Insert into database
            result = await db.inventory.insert_one(item_dict)
            item_dict["_id"] = result.inserted_id
            item_dict["id"] = str(result.inserted_id)
            
            return InventoryItem(**item_dict)
            
        except Exception as e:
            logger.error(f"Error creating inventory item: {str(e)}")
            raise
    
    async def update_inventory_item(
        self, 
        db: AsyncIOMotorDatabase, 
        sku: str, 
        update_data: InventoryItemUpdate
    ) -> Optional[InventoryItem]:
        """Update inventory item"""
        try:
            # Get current item
            current_item = await self.get_inventory_item_by_sku(db, sku)
            if not current_item:
                return None
            
            # Prepare update dict
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
            update_dict["updated_at"] = datetime.utcnow()
            
            # Update stock status if current_stock is being updated
            if "current_stock" in update_dict:
                reorder_level = update_dict.get("reorder_level", current_item.reorder_level)
                if update_dict["current_stock"] == 0:
                    update_dict["status"] = StockStatus.OUT_OF_STOCK
                elif update_dict["current_stock"] <= reorder_level:
                    update_dict["status"] = StockStatus.LOW_STOCK
                else:
                    update_dict["status"] = StockStatus.IN_STOCK
            
            # Update in database
            result = await db.inventory.update_one(
                {"sku": sku},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                return await self.get_inventory_item_by_sku(db, sku)
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating inventory item {sku}: {str(e)}")
            raise
    
    async def delete_inventory_item(
        self, 
        db: AsyncIOMotorDatabase, 
        sku: str
    ) -> bool:
        """Delete inventory item"""
        try:
            result = await db.inventory.delete_one({"sku": sku})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting inventory item {sku}: {str(e)}")
            raise
    
    async def record_stock_movement(
        self,
        db: AsyncIOMotorDatabase,
        sku: str,
        movement_type: str,
        quantity: int,
        reason: str,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> StockMovement:
        """Record stock movement and update inventory"""
        try:
            # Validate movement type
            valid_types = ["IN", "OUT", "ADJUSTMENT", "TRANSFER"]
            if movement_type.upper() not in valid_types:
                raise ValueError(f"Invalid movement type. Must be one of: {valid_types}")
            
            # Get current inventory item
            item = await self.get_inventory_item_by_sku(db, sku)
            if not item:
                raise ValueError(f"Inventory item with SKU {sku} not found")
            
            # Calculate new stock level
            previous_stock = item.current_stock
            
            if movement_type.upper() == "OUT":
                new_stock = previous_stock - abs(quantity)
            elif movement_type.upper() == "IN":
                new_stock = previous_stock + abs(quantity)
            elif movement_type.upper() == "ADJUSTMENT":
                new_stock = previous_stock + quantity  # quantity can be negative
            elif movement_type.upper() == "TRANSFER":
                new_stock = previous_stock - abs(quantity)  # Transfer out
            
            # Validate new stock level
            if new_stock < 0:
                raise ValueError(f"Insufficient stock. Current: {previous_stock}, Requested: {abs(quantity)}")
            
            # Create movement record
            movement_dict = {
                "inventory_item_sku": sku,
                "movement_type": movement_type.upper(),
                "quantity": quantity,
                "previous_stock": previous_stock,
                "new_stock": new_stock,
                "reason": reason,
                "reference_number": reference_number,
                "warehouse_id": item.warehouse_id,
                "created_by": created_by,
                "created_at": datetime.utcnow(),
                "notes": notes
            }
            
            # Insert movement record
            movement_result = await db.stock_movements.insert_one(movement_dict)
            movement_dict["_id"] = movement_result.inserted_id
            movement_dict["id"] = str(movement_result.inserted_id)
            
            # Update inventory stock
            update_data = InventoryItemUpdate(current_stock=new_stock)
            await self.update_inventory_item(db, sku, update_data)
            
            return StockMovement(**movement_dict)
            
        except Exception as e:
            logger.error(f"Error recording stock movement for {sku}: {str(e)}")
            raise
    
    async def get_stock_movements(
        self,
        db: AsyncIOMotorDatabase,
        sku: str,
        limit: int = 50
    ) -> List[StockMovement]:
        """Get stock movement history for an item"""
        try:
            cursor = db.stock_movements.find(
                {"inventory_item_sku": sku}
            ).sort("created_at", -1).limit(limit)
            
            movements_data = await cursor.to_list(length=limit)
            movements = []
            
            for movement_data in movements_data:
                movement_data["id"] = str(movement_data["_id"])
                movements.append(StockMovement(**movement_data))
            
            return movements
            
        except Exception as e:
            logger.error(f"Error fetching stock movements for {sku}: {str(e)}")
            raise
    
    async def get_low_stock_items(
        self,
        db: AsyncIOMotorDatabase,
        warehouse_id: Optional[str] = None
    ) -> List[InventoryItem]:
        """Get items at or below reorder level"""
        try:
            query = {"$expr": {"$lte": ["$current_stock", "$reorder_level"]}}
            
            if warehouse_id:
                query["warehouse_id"] = warehouse_id
            
            cursor = db.inventory.find(query)
            items_data = await cursor.to_list(length=None)
            
            items = []
            for item_data in items_data:
                item_data["id"] = str(item_data["_id"])
                items.append(InventoryItem(**item_data))
            
            return items
            
        except Exception as e:
            logger.error(f"Error fetching low stock items: {str(e)}")
            raise
    
    async def get_reorder_suggestions(
        self,
        db: AsyncIOMotorDatabase,
        warehouse_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate reorder suggestions"""
        try:
            # Get low stock items
            low_stock_items = await self.get_low_stock_items(db, warehouse_id)
            
            suggestions = []
            
            for item in low_stock_items:
                # Calculate suggested order quantity
                days_since_last_restock = 30  # Default if no last restock date
                if item.last_restocked:
                    days_since_last_restock = (datetime.utcnow() - item.last_restocked).days
                
                # Basic reorder calculation
                suggested_quantity = max(
                    item.reorder_quantity,
                    item.minimum_stock - item.current_stock
                )
                
                suggestion = {
                    "sku": item.sku,
                    "name": item.name,
                    "current_stock": item.current_stock,
                    "reorder_level": item.reorder_level,
                    "suggested_quantity": suggested_quantity,
                    "supplier_id": item.supplier_id,
                    "estimated_cost": suggested_quantity * item.cost_price,
                    "priority": "high" if item.current_stock == 0 else "medium",
                    "days_since_restock": days_since_last_restock
                }
                
                suggestions.append(suggestion)
            
            # Sort by priority and stock level
            suggestions.sort(key=lambda x: (x["priority"] == "high", -x["current_stock"]), reverse=True)
            
            return {
                "total_suggestions": len(suggestions),
                "total_estimated_cost": sum(s["estimated_cost"] for s in suggestions),
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Error generating reorder suggestions: {str(e)}")
            raise
    
    async def deduplicate_inventory(
        self,
        db: AsyncIOMotorDatabase,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """Identify and optionally remove duplicate inventory items"""
        try:
            # Get all inventory items
            cursor = db.inventory.find({})
            items_data = await cursor.to_list(length=None)
            
            duplicates = []
            items_by_similarity = {}
            
            # Group items by similar names and descriptions
            for item_data in items_data:
                key = self._generate_similarity_key(item_data.get("name", ""), item_data.get("description", ""))
                
                if key not in items_by_similarity:
                    items_by_similarity[key] = []
                items_by_similarity[key].append(item_data)
            
            # Find potential duplicates
            for key, items in items_by_similarity.items():
                if len(items) > 1:
                    # Calculate similarity scores
                    for i in range(len(items)):
                        for j in range(i + 1, len(items)):
                            similarity = self._calculate_similarity(items[i], items[j])
                            if similarity > 0.8:  # 80% similarity threshold
                                duplicates.append({
                                    "items": [
                                        {"sku": items[i]["sku"], "name": items[i]["name"]},
                                        {"sku": items[j]["sku"], "name": items[j]["name"]}
                                    ],
                                    "similarity_score": similarity,
                                    "suggested_action": "merge" if similarity > 0.95 else "review"
                                })
            
            result = {
                "total_items_analyzed": len(items_data),
                "potential_duplicates_found": len(duplicates),
                "duplicates": duplicates,
                "dry_run": dry_run
            }
            
            if not dry_run:
                # TODO: Implement actual deduplication logic
                # This would require careful merging of stock levels, movements, etc.
                result["items_merged"] = 0
                result["message"] = "Deduplication not yet implemented in production mode"
            
            return result
            
        except Exception as e:
            logger.error(f"Error deduplicating inventory: {str(e)}")
            raise
    
    def _generate_similarity_key(self, name: str, description: str) -> str:
        """Generate a key for grouping similar items"""
        # Normalize and create key from first few words
        text = f"{name} {description}".lower()
        words = re.findall(r'\b\w+\b', text)
        return " ".join(sorted(words[:3]))  # Use first 3 words, sorted
    
    def _calculate_similarity(self, item1: Dict, item2: Dict) -> float:
        """Calculate similarity between two inventory items"""
        # Compare names
        name_similarity = SequenceMatcher(None, item1.get("name", "").lower(), item2.get("name", "").lower()).ratio()
        
        # Compare descriptions
        desc_similarity = SequenceMatcher(None, item1.get("description", "").lower(), item2.get("description", "").lower()).ratio()
        
        # Compare categories
        category_similarity = 1.0 if item1.get("category") == item2.get("category") else 0.0
        
        # Weighted average
        return (name_similarity * 0.5 + desc_similarity * 0.3 + category_similarity * 0.2)
    
    async def get_inventory_summary(
        self,
        db: AsyncIOMotorDatabase,
        warehouse_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get inventory analytics summary"""
        try:
            # Build match criteria
            match_criteria = {}
            if warehouse_id:
                match_criteria["warehouse_id"] = warehouse_id
            
            # Aggregation pipeline
            pipeline = [
                {"$match": match_criteria},
                {
                    "$group": {
                        "_id": None,
                        "total_items": {"$sum": 1},
                        "total_stock_value": {"$sum": {"$multiply": ["$current_stock", "$cost_price"]}},
                        "total_selling_value": {"$sum": {"$multiply": ["$current_stock", "$selling_price"]}},
                        "low_stock_items": {
                            "$sum": {
                                "$cond": [
                                    {"$lte": ["$current_stock", "$reorder_level"]},
                                    1,
                                    0
                                ]
                            }
                        },
                        "out_of_stock_items": {
                            "$sum": {
                                "$cond": [
                                    {"$eq": ["$current_stock", 0]},
                                    1,
                                    0
                                ]
                            }
                        },
                        "categories": {"$addToSet": "$category"}
                    }
                }
            ]
            
            cursor = db.inventory.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                summary = result[0]
                summary["total_categories"] = len(summary["categories"])
                summary["stock_turnover_ratio"] = 0  # TODO: Calculate based on movements
                summary["warehouse_id"] = warehouse_id
                del summary["_id"]
                del summary["categories"]  # Remove the categories list from response
            else:
                summary = {
                    "total_items": 0,
                    "total_stock_value": 0,
                    "total_selling_value": 0,
                    "low_stock_items": 0,
                    "out_of_stock_items": 0,
                    "total_categories": 0,
                    "stock_turnover_ratio": 0,
                    "warehouse_id": warehouse_id
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating inventory summary: {str(e)}")
            raise
    
    async def get_categories(self, db: AsyncIOMotorDatabase) -> List[str]:
        """Get list of all inventory categories"""
        try:
            categories = await db.inventory.distinct("category")
            return sorted(categories)
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            raise

# Global inventory service instance
inventory_service = InventoryService()
