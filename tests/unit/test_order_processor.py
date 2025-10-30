"""
Unit tests for order_processor module.
Tests INV-F-010, INV-F-011, INV-F-012, INV-F-031.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from src.order_processor import OrderProcessor
from src.product_manager import ProductManager
from src.supplier_manager import SupplierManager
from src.storage import StorageManager
from src.logger import LogManager


class TestOrderProcessor:
    """Test order processor."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def managers(self, temp_db):
        """Create all managers with temporary database."""
        storage = StorageManager(temp_db)
        logger = LogManager(storage)
        product_manager = ProductManager(storage, logger)
        supplier_manager = SupplierManager(storage, logger)
        order_processor = OrderProcessor(storage, logger, product_manager)
        
        return {
            'storage': storage,
            'product_manager': product_manager,
            'supplier_manager': supplier_manager,
            'order_processor': order_processor
        }

    def test_create_sales_order_success(self, managers):
        """Test creating sales order successfully (INV-F-010)."""
        pm = managers['product_manager']
        op = managers['order_processor']
        
        # Add product with stock
        product_id = pm.add_product("PROD001", "Product", 10.00, "Cat", 100)
        
        # Create sales order
        order_id = op.create_sales_order(product_id, 5)
        
        assert order_id is not None
        assert order_id > 0
        
        # Verify stock decreased
        product = pm.get_product(product_id)
        assert product['stock'] == 95

    def test_create_sales_order_insufficient_stock(self, managers):
        """Test creating sales order with insufficient stock (INV-F-011)."""
        pm = managers['product_manager']
        op = managers['order_processor']
        
        # Add product with limited stock
        product_id = pm.add_product("PROD001", "Product", 10.00, "Cat", 5)
        
        # Try to order more than available
        order_id = op.create_sales_order(product_id, 10)
        
        # Should return None (insufficient stock)
        assert order_id is None
        
        # Stock should remain unchanged
        product = pm.get_product(product_id)
        assert product['stock'] == 5

    def test_create_sales_order_invalid_quantity(self, managers):
        """Test creating sales order with invalid quantity."""
        pm = managers['product_manager']
        op = managers['order_processor']
        
        product_id = pm.add_product("PROD001", "Product", 10.00, "Cat", 100)
        
        # Negative quantity
        with pytest.raises(ValueError):
            op.create_sales_order(product_id, -5)
        
        # Zero quantity
        with pytest.raises(ValueError):
            op.create_sales_order(product_id, 0)

    def test_create_sales_order_product_not_found(self, managers):
        """Test creating sales order for non-existent product."""
        op = managers['order_processor']
        
        with pytest.raises(ValueError):
            op.create_sales_order(99999, 5)

    def test_create_purchase_order_success(self, managers):
        """Test creating purchase order successfully (INV-F-012)."""
        pm = managers['product_manager']
        sm = managers['supplier_manager']
        op = managers['order_processor']
        
        # Add product and supplier
        product_id = pm.add_product("PROD001", "Product", 10.00, "Cat", 50)
        supplier_id = sm.add_supplier("Supplier", "Contact", "email@test.com")
        
        # Create purchase order
        order_id = op.create_purchase_order(product_id, supplier_id, 20, 8.00)
        
        assert order_id is not None
        assert order_id > 0
        
        # Verify stock increased
        product = pm.get_product(product_id)
        assert product['stock'] == 70

    def test_create_purchase_order_invalid_quantity(self, managers):
        """Test creating purchase order with invalid quantity."""
        pm = managers['product_manager']
        sm = managers['supplier_manager']
        op = managers['order_processor']
        
        product_id = pm.add_product("PROD001", "Product", 10.00, "Cat", 50)
        supplier_id = sm.add_supplier("Supplier", "Contact", "email@test.com")
        
        # Negative quantity
        with pytest.raises(ValueError):
            op.create_purchase_order(product_id, supplier_id, -10, 8.00)

    def test_create_purchase_order_invalid_price(self, managers):
        """Test creating purchase order with invalid unit price."""
        pm = managers['product_manager']
        sm = managers['supplier_manager']
        op = managers['order_processor']
        
        product_id = pm.add_product("PROD001", "Product", 10.00, "Cat", 50)
        supplier_id = sm.add_supplier("Supplier", "Contact", "email@test.com")
        
        # Negative price
        with pytest.raises(ValueError):
            op.create_purchase_order(product_id, supplier_id, 10, -5.00)

    def test_get_sales_orders(self, managers):
        """Test getting sales orders."""
        pm = managers['product_manager']
        op = managers['order_processor']
        
        product_id = pm.add_product("PROD001", "Product", 10.00, "Cat", 100)
        op.create_sales_order(product_id, 5)
        op.create_sales_order(product_id, 3)
        
        orders = op.get_sales_orders()
        
        assert len(orders) >= 2

    def test_get_purchase_orders(self, managers):
        """Test getting purchase orders."""
        pm = managers['product_manager']
        sm = managers['supplier_manager']
        op = managers['order_processor']
        
        product_id = pm.add_product("PROD001", "Product", 10.00, "Cat", 50)
        supplier_id = sm.add_supplier("Supplier", "Contact", "email@test.com")
        
        op.create_purchase_order(product_id, supplier_id, 10, 8.00)
        op.create_purchase_order(product_id, supplier_id, 15, 7.50)
        
        orders = op.get_purchase_orders()
        
        assert len(orders) >= 2

    def test_get_sales_report(self, managers):
        """Test generating sales report (INV-F-031)."""
        pm = managers['product_manager']
        op = managers['order_processor']
        
        product_id = pm.add_product("PROD001", "Product", 10.00, "Cat", 100)
        
        op.create_sales_order(product_id, 5)  # $50
        op.create_sales_order(product_id, 3)  # $30
        
        report = op.get_sales_report()
        
        assert report['total_orders'] >= 2
        assert report['total_revenue'] >= 80.00
        assert report['total_units'] >= 8

    def test_get_purchase_report(self, managers):
        """Test generating purchase report (INV-F-031)."""
        pm = managers['product_manager']
        sm = managers['supplier_manager']
        op = managers['order_processor']
        
        product_id = pm.add_product("PROD001", "Product", 10.00, "Cat", 50)
        supplier_id = sm.add_supplier("Supplier", "Contact", "email@test.com")
        
        op.create_purchase_order(product_id, supplier_id, 10, 8.00)  # $80
        op.create_purchase_order(product_id, supplier_id, 15, 7.50)  # $112.50
        
        report = op.get_purchase_report()
        
        assert report['total_orders'] >= 2
        assert report['total_cost'] >= 192.50
        assert report['total_units'] >= 25

    def test_sales_order_total_price_calculation(self, managers):
        """Test that total price is calculated correctly."""
        pm = managers['product_manager']
        op = managers['order_processor']
        
        product_id = pm.add_product("PROD001", "Product", 12.50, "Cat", 100)
        order_id = op.create_sales_order(product_id, 4)
        
        # Get order from database
        orders = op.get_sales_orders()
        order = [o for o in orders if o['id'] == order_id][0]
        
        assert order['total_price'] == 50.00  # 12.50 * 4

    def test_purchase_order_total_price_calculation(self, managers):
        """Test that purchase order total is calculated correctly."""
        pm = managers['product_manager']
        sm = managers['supplier_manager']
        op = managers['order_processor']
        
        product_id = pm.add_product("PROD001", "Product", 10.00, "Cat", 50)
        supplier_id = sm.add_supplier("Supplier", "Contact", "email@test.com")
        
        order_id = op.create_purchase_order(product_id, supplier_id, 15, 7.25)
        
        # Get order from database
        orders = op.get_purchase_orders()
        order = [o for o in orders if o['id'] == order_id][0]
        
        assert order['total_price'] == 108.75  # 15 * 7.25
