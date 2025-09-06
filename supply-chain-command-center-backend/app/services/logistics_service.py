import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Location:
    id: str
    name: str
    latitude: float
    longitude: float
    address: str
    type: str = "customer"  # warehouse, customer, supplier

@dataclass
class Vehicle:
    id: str
    capacity: float
    cost_per_km: float
    max_distance: float = 1000.0
    start_location: Optional[str] = None
    end_location: Optional[str] = None

@dataclass
class Delivery:
    id: str
    customer_location_id: str
    demand: float
    time_window_start: Optional[int] = None  # Minutes from start of day
    time_window_end: Optional[int] = None
    service_time: int = 30  # Minutes to complete delivery
    priority: int = 1  # 1 = normal, 2 = high, 3 = urgent

class LogisticsService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    async def optimize_delivery_routes(
        self,
        db: AsyncIOMotorDatabase,
        warehouse_id: str,
        delivery_requests: List[Dict[str, Any]],
        vehicles: List[Dict[str, Any]],
        optimization_type: str = "minimize_distance"
    ) -> Dict[str, Any]:
        """Optimize delivery routes using OR-Tools VRP solver"""
        try:
            # Parse and validate input data
            locations, vehicles_data, deliveries = await self._prepare_optimization_data(
                db, warehouse_id, delivery_requests, vehicles
            )
            
            if len(locations) < 2 or len(vehicles_data) == 0:
                return {
                    "error": "Insufficient data for route optimization",
                    "locations_count": len(locations),
                    "vehicles_count": len(vehicles_data)
                }
            
            # Calculate distance matrix
            distance_matrix = await self._calculate_distance_matrix(locations)
            
            # Create optimization model
            optimization_result = await self._solve_vrp(
                locations=locations,
                vehicles=vehicles_data,
                deliveries=deliveries,
                distance_matrix=distance_matrix,
                optimization_type=optimization_type
            )
            
            if not optimization_result["success"]:
                return optimization_result
            
            # Format results for API response
            result = await self._format_optimization_results(
                optimization_result,
                locations,
                vehicles_data,
                deliveries
            )
            
            # Store optimization results
            await self._store_optimization_results(db, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in route optimization: {str(e)}")
            return {"error": f"Route optimization failed: {str(e)}"}
    
    async def calculate_delivery_time_estimate(
        self,
        db: AsyncIOMotorDatabase,
        from_location_id: str,
        to_location_id: str,
        traffic_factor: float = 1.0
    ) -> Dict[str, Any]:
        """Calculate estimated delivery time between two locations"""
        try:
            # For demo purposes, using mock locations
            # In production, you'd fetch from database
            mock_locations = {
                "WH001": {"latitude": 40.7128, "longitude": -74.0060, "name": "NYC Warehouse"},
                "CUST001": {"latitude": 40.7589, "longitude": -73.9851, "name": "Customer 1"},
                "CUST002": {"latitude": 40.6892, "longitude": -74.0445, "name": "Customer 2"}
            }
            
            from_location = mock_locations.get(from_location_id)
            to_location = mock_locations.get(to_location_id)
            
            if not from_location or not to_location:
                return {"error": "Location not found"}
            
            # Calculate distance
            distance_km = self._calculate_haversine_distance(
                from_location["latitude"],
                from_location["longitude"],
                to_location["latitude"],
                to_location["longitude"]
            )
            
            # Estimate time (assuming average speed of 50 km/h in urban areas)
            base_time_hours = distance_km / 50.0
            adjusted_time_hours = base_time_hours * traffic_factor
            
            return {
                "from_location": from_location_id,
                "to_location": to_location_id,
                "distance_km": round(distance_km, 2),
                "estimated_time_hours": round(adjusted_time_hours, 2),
                "estimated_time_minutes": round(adjusted_time_hours * 60, 0),
                "traffic_factor": traffic_factor
            }
            
        except Exception as e:
            logger.error(f"Error calculating delivery time: {str(e)}")
            return {"error": str(e)}
    
    async def optimize_warehouse_allocation(
        self,
        db: AsyncIOMotorDatabase,
        orders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Optimize which warehouse should fulfill each order"""
        try:
            # Get all warehouses with inventory
            warehouses = await self._get_warehouses_with_inventory(db)
            
            if not warehouses:
                return {"error": "No warehouses with inventory found"}
            
            allocations = []
            total_cost = 0.0
            
            for order in orders:
                best_allocation = await self._find_best_warehouse_for_order(
                    db, order, warehouses
                )
                
                if best_allocation:
                    allocations.append(best_allocation)
                    total_cost += best_allocation["estimated_cost"]
                else:
                    allocations.append({
                        "order_id": order.get("id"),
                        "error": "No suitable warehouse found"
                    })
            
            return {
                "total_orders": len(orders),
                "successful_allocations": len([a for a in allocations if "error" not in a]),
                "failed_allocations": len([a for a in allocations if "error" in a]),
                "total_estimated_cost": round(total_cost, 2),
                "allocations": allocations,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in warehouse allocation optimization: {str(e)}")
            return {"error": str(e)}
    
    async def _prepare_optimization_data(
        self,
        db: AsyncIOMotorDatabase,
        warehouse_id: str,
        delivery_requests: List[Dict],
        vehicles: List[Dict]
    ) -> Tuple[List[Location], List[Vehicle], List[Delivery]]:
        """Prepare and validate data for optimization"""
        
        # Get warehouse location (with fallback for demo)
        warehouse = await db.warehouses.find_one({"warehouse_id": warehouse_id})
        if not warehouse:
            # Use mock data for demo
            warehouse = {
                "warehouse_id": warehouse_id,
                "name": f"Warehouse {warehouse_id}",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "address": "123 Main St, NYC"
            }
        
        locations = [
            Location(
                id=warehouse_id,
                name=warehouse.get("name", "Warehouse"),
                latitude=warehouse.get("latitude", 40.7128),
                longitude=warehouse.get("longitude", -74.0060),
                address=warehouse.get("address", ""),
                type="warehouse"
            )
        ]
        
        # Add customer locations
        for i, request in enumerate(delivery_requests):
            customer_id = request.get("customer_id", f"CUST_{i}")
            locations.append(
                Location(
                    id=customer_id,
                    name=request.get("customer_name", f"Customer {customer_id}"),
                    latitude=request.get("latitude", 40.7128 + (i * 0.01)),
                    longitude=request.get("longitude", -74.0060 + (i * 0.01)),
                    address=request.get("address", f"Address {i}"),
                    type="customer"
                )
            )
        
        # Parse vehicles
        vehicles_data = []
        for i, vehicle_data in enumerate(vehicles):
            vehicles_data.append(
                Vehicle(
                    id=vehicle_data.get("id", f"vehicle_{i}"),
                    capacity=vehicle_data.get("capacity", 1000.0),
                    cost_per_km=vehicle_data.get("cost_per_km", 1.0),
                    max_distance=vehicle_data.get("max_distance", 500.0),
                    start_location=warehouse_id,
                    end_location=warehouse_id
                )
            )
        
        # Parse deliveries
        deliveries = []
        for i, request in enumerate(delivery_requests):
            deliveries.append(
                Delivery(
                    id=request.get("id", f"delivery_{i}"),
                    customer_location_id=request.get("customer_id", f"CUST_{i}"),
                    demand=request.get("weight", float(i + 1) * 10),  # Mock demand
                    time_window_start=request.get("time_window_start"),
                    time_window_end=request.get("time_window_end"),
                    service_time=request.get("service_time", 30),
                    priority=request.get("priority", 1)
                )
            )
        
        return locations, vehicles_data, deliveries
    
    async def _calculate_distance_matrix(self, locations: List[Location]) -> List[List[float]]:
        """Calculate distance matrix between all locations"""
        loop = asyncio.get_event_loop()
        
        def calculate():
            n = len(locations)
            matrix = [[0.0 for _ in range(n)] for _ in range(n)]
            
            for i in range(n):
                for j in range(n):
                    if i != j:
                        distance = self._calculate_haversine_distance(
                            locations[i].latitude,
                            locations[i].longitude,
                            locations[j].latitude,
                            locations[j].longitude
                        )
                        matrix[i][j] = distance * 1000  # Convert to meters for OR-Tools
                    else:
                        matrix[i][j] = 0
            
            return matrix
        
        return await loop.run_in_executor(self.executor, calculate)
    
    def _calculate_haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on earth in kilometers"""
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r
    
    async def _solve_vrp(
        self,
        locations: List[Location],
        vehicles: List[Vehicle],
        deliveries: List[Delivery],
        distance_matrix: List[List[float]],
        optimization_type: str
    ) -> Dict[str, Any]:
        """Solve Vehicle Routing Problem using OR-Tools"""
        loop = asyncio.get_event_loop()
        
        def solve():
            try:
                # Create the routing index manager
                manager = pywrapcp.RoutingIndexManager(
                    len(locations),  # Number of locations
                    len(vehicles),   # Number of vehicles
                    0               # Depot index (warehouse)
                )
                
                # Create Routing Model
                routing = pywrapcp.RoutingModel(manager)
                
                # Create distance callback
                def distance_callback(from_index, to_index):
                    from_node = manager.IndexToNode(from_index)
                    to_node = manager.IndexToNode(to_index)
                    return int(distance_matrix[from_node][to_node])
                
                transit_callback_index = routing.RegisterTransitCallback(distance_callback)
                routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
                
                # Add capacity constraint
                def demand_callback(from_index):
                    from_node = manager.IndexToNode(from_index)
                    # Warehouse has 0 demand, deliveries have positive demand
                    if from_node == 0:  # Warehouse
                        return 0
                    # Find corresponding delivery
                    for delivery in deliveries:
                        if locations[from_node].id == delivery.customer_location_id:
                            return int(delivery.demand)
                    return 0
                
                demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
                
                # Add capacity constraints for each vehicle
                routing.AddDimensionWithVehicleCapacity(
                    demand_callback_index,
                    0,  # null capacity slack
                    [int(vehicle.capacity) for vehicle in vehicles],  # vehicle maximum capacities
                    True,  # start cumul to zero
                    'Capacity'
                )
                
                # Add distance constraint
                routing.AddDimension(
                    transit_callback_index,
                    0,  # no slack
                    int(max(v.max_distance * 1000 for v in vehicles)),  # maximum distance per vehicle
                    True,  # start cumul to zero
                    'Distance'
                )
                distance_dimension = routing.GetDimensionOrDie('Distance')
                distance_dimension.SetGlobalSpanCostCoefficient(100)
                
                # Set search parameters
                search_parameters = pywrapcp.DefaultRoutingSearchParameters()
                search_parameters.first_solution_strategy = (
                    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
                )
                search_parameters.local_search_metaheuristic = (
                    routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
                )
                search_parameters.time_limit.FromSeconds(30)  # 30 second limit
                
                # Solve the problem
                solution = routing.SolveWithParameters(search_parameters)
                
                if solution:
                    return {
                        "success": True,
                        "solution": solution,
                        "manager": manager,
                        "routing": routing,
                        "total_distance": solution.ObjectiveValue(),
                        "status": "ROUTING_SUCCESS"
                    }
                else:
                    return {
                        "success": False,
                        "error": "No solution found",
                        "status": "ROUTING_FAIL"
                    }
                    
            except Exception as e:
                logger.error(f"Error in VRP solver: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "status": "SOLVER_ERROR"
                }
        
        return await loop.run_in_executor(self.executor, solve)
    
    async def _format_optimization_results(
        self,
        optimization_result: Dict,
        locations: List[Location],
        vehicles: List[Vehicle],
        deliveries: List[Delivery]
    ) -> Dict[str, Any]:
        """Format optimization results for API response"""
        
        if not optimization_result["success"]:
            return optimization_result
        
        solution = optimization_result["solution"]
        manager = optimization_result["manager"]
        routing = optimization_result["routing"]
        
        routes = []
        total_distance = 0
        total_load = 0
        
        for vehicle_id in range(len(vehicles)):
            index = routing.Start(vehicle_id)
            route_distance = 0
            route_load = 0
            route_stops = []
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                location = locations[node_index]
                
                # Find corresponding delivery if not depot
                delivery_info = None
                if node_index != 0:  # Not depot
                    for delivery in deliveries:
                        if delivery.customer_location_id == location.id:
                            delivery_info = {
                                "delivery_id": delivery.id,
                                "demand": delivery.demand,
                                "service_time": delivery.service_time
                            }
                            route_load += delivery.demand
                            break
                
                route_stops.append({
                    "location_id": location.id,
                    "location_name": location.name,
                    "location_type": location.type,
                    "coordinates": {
                        "latitude": location.latitude,
                        "longitude": location.longitude
                    },
                    "delivery": delivery_info,
                    "arrival_order": len(route_stops) + 1
                })
                
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
            
            # Add final depot
            depot_location = locations[0]
            route_stops.append({
                "location_id": depot_location.id,
                "location_name": depot_location.name,
                "location_type": depot_location.type,
                "coordinates": {
                    "latitude": depot_location.latitude,
                    "longitude": depot_location.longitude
                },
                "delivery": None,
                "arrival_order": len(route_stops) + 1
            })
            
            if len(route_stops) > 2:  # More than just start and end depot
                routes.append({
                    "vehicle_id": vehicles[vehicle_id].id,
                    "vehicle_capacity": vehicles[vehicle_id].capacity,
                    "route_distance_km": round(route_distance / 1000, 2),
                    "route_load": round(route_load, 2),
                    "capacity_utilization": round((route_load / vehicles[vehicle_id].capacity) * 100, 1),
                    "stops": route_stops,
                    "estimated_duration_hours": round((route_distance / 1000) / 50, 2)  # Assuming 50 km/h average speed
                })
                
                total_distance += route_distance
                total_load += route_load
        
        return {
            "success": True,
            "optimization_type": "vehicle_routing_problem",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_routes": len(routes),
                "total_distance_km": round(total_distance / 1000, 2),
                "total_load": round(total_load, 2),
                "vehicles_used": len(routes),
                "total_deliveries": len(deliveries),
                "average_distance_per_route": round((total_distance / 1000) / max(len(routes), 1), 2)
            },
            "routes": routes,
            "optimization_stats": {
                "solver_status": optimization_result["status"],
                "objective_value": optimization_result["total_distance"],
                "locations_count": len(locations),
                "vehicles_count": len(vehicles)
            }
        }
    
    async def _get_warehouses_with_inventory(self, db: AsyncIOMotorDatabase) -> List[Dict]:
        """Get warehouses that have inventory available"""
        try:
            # Aggregate inventory by warehouse
            pipeline = [
                {
                    "$match": {
                        "current_stock": {"$gt": 0},
                        "status": {"$ne": "discontinued"}
                    }
                },
                {
                    "$group": {
                        "_id": "$warehouse_id",
                        "total_items": {"$sum": 1},
                        "total_stock_value": {"$sum": {"$multiply": ["$current_stock", "$cost_price"]}}
                    }
                }
            ]
            
            cursor = db.inventory.aggregate(pipeline)
            inventory_by_warehouse = await cursor.to_list(length=None)
            
            # Get warehouse details
            warehouse_ids = [item["_id"] for item in inventory_by_warehouse]
            warehouses_cursor = db.warehouses.find({"warehouse_id": {"$in": warehouse_ids}})
            warehouses = await warehouses_cursor.to_list(length=None)
            
            # Combine data
            result = []
            for warehouse in warehouses:
                inventory_info = next(
                    (item for item in inventory_by_warehouse if item["_id"] == warehouse["warehouse_id"]),
                    None
                )
                
                if inventory_info:
                    warehouse["inventory_summary"] = {
                        "total_items": inventory_info["total_items"],
                        "total_stock_value": inventory_info["total_stock_value"]
                    }
                    result.append(warehouse)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting warehouses with inventory: {str(e)}")
            return []
    
    async def _find_best_warehouse_for_order(
        self,
        db: AsyncIOMotorDatabase,
        order: Dict,
        warehouses: List[Dict]
    ) -> Optional[Dict]:
        """Find the best warehouse to fulfill a specific order"""
        try:
            customer_lat = order.get("customer_latitude", 40.7589)
            customer_lon = order.get("customer_longitude", -73.9851)
            
            best_option = None
            best_score = float('inf')
            
            for warehouse in warehouses:
                # Check if warehouse has required items in stock
                required_items = order.get("items", [])
                can_fulfill = True
                
                for item in required_items:
                    sku = item.get("sku")
                    quantity = item.get("quantity", 0)
                    
                    # Check inventory
                    inventory_item = await db.inventory.find_one({
                        "sku": sku,
                        "warehouse_id": warehouse["warehouse_id"],
                        "current_stock": {"$gte": quantity}
                    })
                    
                    if not inventory_item:
                        can_fulfill = False
                        break
                
                if not can_fulfill and required_items:  # Only check if items were specified
                    continue
                
                # Calculate distance-based score
                distance = self._calculate_haversine_distance(
                    warehouse.get("latitude", 40.7128),
                    warehouse.get("longitude", -74.0060),
                    customer_lat,
                    customer_lon
                )
                
                # Simple scoring: distance + warehouse utilization factor
                utilization = warehouse.get("current_utilization", 0) / warehouse.get("storage_capacity", 1)
                score = distance + (utilization * 10)  # Prefer less utilized warehouses
                
                if score < best_score:
                    best_score = score
                    best_option = {
                        "order_id": order.get("id"),
                        "warehouse_id": warehouse["warehouse_id"],
                        "warehouse_name": warehouse["name"],
                        "distance_km": round(distance, 2),
                        "estimated_cost": round(distance * 2.0, 2),  # $2 per km estimate
                        "estimated_delivery_time_hours": round(distance / 50, 2),
                        "warehouse_utilization": round(utilization * 100, 1)
                    }
            
            return best_option
            
        except Exception as e:
            logger.error(f"Error finding best warehouse for order: {str(e)}")
            return None
    
    async def _store_optimization_results(self, db: AsyncIOMotorDatabase, results: Dict):
        """Store optimization results in database for future analysis"""
        try:
            if results.get("success"):
                doc = {
                    "optimization_type": "route_optimization",
                    "results": results,
                    "created_at": datetime.utcnow()
                }
                await db.logistics_optimizations.insert_one(doc)
        except Exception as e:
            logger.error(f"Error storing optimization results: {str(e)}")

# Global logistics service instance
logistics_service = LogisticsService()
