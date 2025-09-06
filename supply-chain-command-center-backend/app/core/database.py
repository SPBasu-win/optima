from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.database: AsyncIOMotorDatabase = None

    async def connect_to_mongo(self):
        """Create database connection"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.database = self.client[settings.DATABASE_NAME]
            
            # Test the connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e

    async def close_mongo_connection(self):
        """Close database connection"""
        try:
            if self.client:
                self.client.close()
                logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
            raise e

    async def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Inventory collection indexes
            await self.database.inventory.create_index("sku", unique=True)
            await self.database.inventory.create_index("supplier_id")
            await self.database.inventory.create_index("warehouse_id")
            await self.database.inventory.create_index("category")
            
            # Invoice collection indexes
            await self.database.invoices.create_index("invoice_number", unique=True)
            await self.database.invoices.create_index("supplier_id")
            await self.database.invoices.create_index("created_at")
            await self.database.invoices.create_index("status")
            
            # Supplier collection indexes
            await self.database.suppliers.create_index("supplier_id", unique=True)
            await self.database.suppliers.create_index("name")
            
            # Warehouse collection indexes
            await self.database.warehouses.create_index("warehouse_id", unique=True)
            await self.database.warehouses.create_index("location")
            
            # Demand forecast collection indexes
            await self.database.demand_forecasts.create_index("product_sku")
            await self.database.demand_forecasts.create_index("forecast_date")
            
            # Logistics collection indexes
            await self.database.deliveries.create_index("delivery_id", unique=True)
            await self.database.deliveries.create_index("status")
            await self.database.deliveries.create_index("scheduled_date")
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating database indexes: {e}")
            raise e

# Global database manager instance
db_manager = DatabaseManager()

async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return db_manager.database
