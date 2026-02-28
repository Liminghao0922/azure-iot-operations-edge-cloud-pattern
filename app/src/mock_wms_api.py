"""
Mock WMS (Warehouse Management System) REST API
Based on Step 12.2: Simulating WMS API for testing HTTP Connector

This API simulates a real warehouse system that provides inventory data
via REST endpoints. The HTTP Connector in Azure IoT Operations will
periodically poll this API and forward the data to the MQTT broker.
"""

from flask import Flask, jsonify, request
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


app = Flask(__name__)


# Simulated inventory database
INVENTORY_DB = [
    {
        "warehouseId": "WH-001",
        "warehouseName": "Main Distribution Center",
        "location": "Shanghai",
        "lastUpdated": None,
        "items": [
            {
                "sku": "PROD-2024-001",
                "name": "Industrial Sensor Type A",
                "quantity": random.randint(50, 500),
                "reorderLevel": 100,
                "unit": "pieces"
            },
            {
                "sku": "PROD-2024-002",
                "name": "Control Module B",
                "quantity": random.randint(20, 200),
                "reorderLevel": 50,
                "unit": "pieces"
            },
            {
                "sku": "PROD-2024-003",
                "name": "Network Gateway C",
                "quantity": random.randint(10, 100),
                "reorderLevel": 20,
                "unit": "pieces"
            },
            {
                "sku": "PROD-2024-004",
                "name": "Power Supply Unit",
                "quantity": random.randint(100, 800),
                "reorderLevel": 150,
                "unit": "pieces"
            },
            {
                "sku": "PROD-2024-005",
                "name": "Cabling & Accessories",
                "quantity": random.randint(500, 2000),
                "reorderLevel": 300,
                "unit": "meters"
            }
        ]
    },
    {
        "warehouseId": "WH-002",
        "warehouseName": "Regional Hub",
        "location": "Beijing",
        "lastUpdated": None,
        "items": [
            {
                "sku": "PROD-2024-001",
                "name": "Industrial Sensor Type A",
                "quantity": random.randint(30, 300),
                "reorderLevel": 100,
                "unit": "pieces"
            },
            {
                "sku": "PROD-2024-003",
                "name": "Network Gateway C",
                "quantity": random.randint(15, 120),
                "reorderLevel": 20,
                "unit": "pieces"
            }
        ]
    }
]


def generate_inventory_response() -> List[Dict[str, Any]]:
    """Generate inventory response with current timestamp"""
    response = []
    
    for warehouse in INVENTORY_DB:
        warehouse_data = {
            "warehouseId": warehouse["warehouseId"],
            "warehouseName": warehouse["warehouseName"],
            "location": warehouse["location"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "inventoryItems": []
        }
        
        # Add items with slightly randomized quantities
        for item in warehouse["items"]:
            item_data = {
                "sku": item["sku"],
                "name": item["name"],
                "quantity": item["quantity"] + random.randint(-5, 5),
                "reorderLevel": item["reorderLevel"],
                "unit": item["unit"],
                "lowStock": item["quantity"] < item["reorderLevel"],
                "lastStocktake": (
                    datetime.utcnow() - timedelta(hours=random.randint(1, 72))
                ).isoformat() + "Z"
            }
            warehouse_data["inventoryItems"].append(item_data)
        
        response.append(warehouse_data)
    
    return response


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Mock WMS API",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    """
    Get all inventory data
    
    Query Parameters:
        - warehouse_id: Filter by warehouse (optional)
        - include_details: Include detailed item information (optional)
    
    Returns:
        JSON array of warehouse inventory
    """
    warehouse_id = request.args.get("warehouse_id")
    
    inventory = generate_inventory_response()
    
    # Filter by warehouse if specified
    if warehouse_id:
        inventory = [w for w in inventory if w["warehouseId"] == warehouse_id]
    
    return jsonify({
        "success": True,
        "data": inventory,
        "count": len(inventory),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@app.route("/api/inventory/<warehouse_id>", methods=["GET"])
def get_warehouse_inventory(warehouse_id: str):
    """Get inventory for specific warehouse"""
    inventory = generate_inventory_response()
    warehouse = next((w for w in inventory if w["warehouseId"] == warehouse_id), None)
    
    if not warehouse:
        return jsonify({
            "success": False,
            "error": f"Warehouse {warehouse_id} not found",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 404
    
    return jsonify({
        "success": True,
        "data": warehouse,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@app.route("/api/inventory/<warehouse_id>/low-stock", methods=["GET"])
def get_low_stock_items(warehouse_id: str):
    """Get items with low stock for specific warehouse"""
    inventory = generate_inventory_response()
    warehouse = next((w for w in inventory if w["warehouseId"] == warehouse_id), None)
    
    if not warehouse:
        return jsonify({
            "success": False,
            "error": f"Warehouse {warehouse_id} not found"
        }), 404
    
    low_stock_items = [item for item in warehouse["inventoryItems"] if item["lowStock"]]
    
    return jsonify({
        "success": True,
        "warehouseId": warehouse_id,
        "warehouseName": warehouse["warehouseName"],
        "lowStockItems": low_stock_items,
        "count": len(low_stock_items),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@app.route("/api/inventory/sku/<sku>", methods=["GET"])
def get_sku_inventory(sku: str):
    """Get inventory for specific SKU across all warehouses"""
    inventory = generate_inventory_response()
    
    result = []
    for warehouse in inventory:
        item = next((i for i in warehouse["inventoryItems"] if i["sku"] == sku), None)
        if item:
            result.append({
                "warehouseId": warehouse["warehouseId"],
                "warehouseName": warehouse["warehouseName"],
                "location": warehouse["location"],
                **item
            })
    
    return jsonify({
        "success": True,
        "sku": sku,
        "warehouses": result,
        "totalQuantity": sum(item["quantity"] for item in result),
        "count": len(result),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@app.route("/api/status", methods=["GET"])
def get_status():
    """Get system status and metrics"""
    inventory = generate_inventory_response()
    
    # Calculate metrics
    total_warehouses = len(inventory)
    total_items = sum(len(w["inventoryItems"]) for w in inventory)
    total_quantity = sum(
        sum(item["quantity"] for item in w["inventoryItems"])
        for w in inventory
    )
    low_stock_count = sum(
        sum(1 for item in w["inventoryItems"] if item["lowStock"])
        for w in inventory
    )
    
    return jsonify({
        "success": True,
        "metrics": {
            "totalWarehouses": total_warehouses,
            "totalSkus": total_items,
            "totalInventoryUnits": total_quantity,
            "lowStockItems": low_stock_count,
            "lastUpdate": datetime.utcnow().isoformat() + "Z"
        },
        "version": "1.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


if __name__ == "__main__":
    print("=" * 60)
    print("Mock WMS API Server Starting")
    print("=" * 60)
    print("\nAvailable Endpoints:")
    print("  GET  /health                        - Health check")
    print("  GET  /api/inventory                 - All inventory")
    print("  GET  /api/inventory/<warehouse_id>  - Warehouse inventory")
    print("  GET  /api/inventory/<wh>/low-stock  - Low stock items")
    print("  GET  /api/inventory/sku/<sku>       - SKU across warehouses")
    print("  GET  /api/status                    - System status")
    print("\nExample:")
    print("  curl http://localhost:8080/api/inventory")
    print("  curl http://localhost:8080/api/inventory/WH-001")
    print("  curl http://localhost:8080/api/inventory/WH-001/low-stock")
    print("\n" + "=" * 60)
    
    app.run(host="0.0.0.0", port=8080, debug=False)
