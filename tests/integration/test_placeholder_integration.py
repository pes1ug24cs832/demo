"""
Integration tests for IMS.
Tests cross-module workflows and persistence (INV-NF-002).
"""

import pytest
import tempfile
import os
from src.storage import StorageManager
from src.auth import AuthManager
from src.logger import LogManager
from src.product_manager import ProductManager
from src.supplier_manager import SupplierManager
from src.order_processor import OrderProcessor


class TestProductOrderIntegration:
    """Test product and order integration."""

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
        """Create all managers."""
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

    def test_create_product_then_sales_order_reduces_stock(self, managers):
        """Test creating product and sales order reduces stock correctly."""
        pm = managers['product_manager']
        op = managers['order_processor']
        
        # Create product
        product_id = pm.add_product("LAPTOP001", "Gaming Laptop", 1299.99, "Electronics", 20)
        
        # Verify initial stock
        product = pm.get_product(product_id)
        assert product['stock'] == 20
        
        # Create sales order
        order_id = op.create_sales_order(product_id, 5)
        
        assert order_id is not None
        
        # Verify stock reduced
        product = pm.get_product(product_id)
        assert product['stock'] == 15

    def test_create_product_then_purchase_order_increases_stock(self, managers):
        """Test creating product and purchase order increases stock correctly."""
        pm = managers['product_manager']
        sm = managers['supplier_manager']
        op = managers['order_processor']
        
        # Create product and supplier
        product_id = pm.add_product("MOUSE001", "Wireless Mouse", 29.99, "Electronics", 50)
        supplier_id = sm.add_supplier("Tech Supplies Inc", "John Doe", "john@techsupplies.com")
        
        # Verify initial stock
        product = pm.get_product(product_id)
        assert product['stock'] == 50
        
        # Create purchase order
        order_id = op.create_purchase_order(product_id, supplier_id, 25, 18.00)
        
        assert order_id is not None
        
        # Verify stock increased
        product = pm.get_product(product_id)
        assert product['stock'] == 75

    def test_multiple_sales_orders_reduce_stock_correctly(self, managers):
        """Test multiple sales orders reduce stock correctly."""
        pm = managers['product_manager']
        op = managers['order_processor']
        
        # Create product
        product_id = pm.add_product("KEYBOARD001", "Mechanical Keyboard", 89.99, "Electronics", 100)
        
        # Create multiple sales orders
        op.create_sales_order(product_id, 10)
        op.create_sales_order(product_id, 15)
        op.create_sales_order(product_id, 20)
        
        # Verify final stock
        product = pm.get_product(product_id)
        assert product['stock'] == 55  # 100 - 10 - 15 - 20

    def test_sales_order_prevents_overselling(self, managers):
        """Test that sales order prevents overselling (INV-F-011)."""
        pm = managers['product_manager']
        op = managers['order_processor']
        
        # Create product with limited stock
        product_id = pm.add_product("LIMITED001", "Limited Item", 199.99, "Special", 10)
        
        # Try to create order for more than available
        order_id = op.create_sales_order(product_id, 15)
        
        # Should return None
        assert order_id is None
        
        # Stock should remain unchanged
        product = pm.get_product(product_id)
        assert product['stock'] == 10


class TestPersistenceIntegration:
    """Test data persistence across database reconnections (INV-NF-002)."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_product_persists_after_restart(self, temp_db):
        """Test that product data persists after database reconnection."""
        # Create product
        storage1 = StorageManager(temp_db)
        logger1 = LogManager(storage1)
        pm1 = ProductManager(storage1, logger1)
        
        product_id = pm1.add_product("PERSIST001", "Persistent Product", 49.99, "Test", 100)
        
        # Close and reopen database
        del pm1
        del logger1
        del storage1
        
        # Create new instances
        storage2 = StorageManager(temp_db)
        logger2 = LogManager(storage2)
        pm2 = ProductManager(storage2, logger2)
        
        # Verify product still exists
        product = pm2.get_product(product_id)
        
        assert product is not None
        assert product['sku'] == "PERSIST001"
        assert product['name'] == "Persistent Product"
        assert product['price'] == 49.99
        assert product['stock'] == 100

    def test_order_history_persists(self, temp_db):
        """Test that order history persists after restart."""
        # Create initial data
        storage1 = StorageManager(temp_db)
        logger1 = LogManager(storage1)
        pm1 = ProductManager(storage1, logger1)
        op1 = OrderProcessor(storage1, logger1, pm1)
        
        product_id = pm1.add_product("ORDER001", "Order Test", 25.00, "Test", 100)
        op1.create_sales_order(product_id, 10)
        op1.create_sales_order(product_id, 5)
        
        # Close and reopen
        del op1
        del pm1
        del logger1
        del storage1
        
        # Verify orders persist
        storage2 = StorageManager(temp_db)
        logger2 = LogManager(storage2)
        pm2 = ProductManager(storage2, logger2)
        op2 = OrderProcessor(storage2, logger2, pm2)
        
        orders = op2.get_sales_orders()
        
        assert len(orders) >= 2

    def test_supplier_persists_after_restart(self, temp_db):
        """Test that supplier data persists."""
        # Create supplier
        storage1 = StorageManager(temp_db)
        logger1 = LogManager(storage1)
        sm1 = SupplierManager(storage1, logger1)
        
        supplier_id = sm1.add_supplier(
            "Persistent Supplier",
            "Jane Smith",
            "jane@supplier.com",
            "555-9876",
            "456 Supply Ave"
        )
        
        # Close and reopen
        del sm1
        del logger1
        del storage1
        
        # Verify supplier exists
        storage2 = StorageManager(temp_db)
        logger2 = LogManager(storage2)
        sm2 = SupplierManager(storage2, logger2)
        
        supplier = sm2.get_supplier(supplier_id)
        
        assert supplier is not None
        assert supplier['name'] == "Persistent Supplier"
        assert supplier['contact_person'] == "Jane Smith"
        assert supplier['email'] == "jane@supplier.com"


class TestAuthLoggingIntegration:
    """Test authentication and logging integration."""

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
        """Create managers."""
        storage = StorageManager(temp_db)
        auth = AuthManager(storage)
        logger = LogManager(storage)
        product_manager = ProductManager(storage, logger)
        
        return {
            'auth': auth,
            'logger': logger,
            'product_manager': product_manager
        }

    def test_admin_actions_are_logged(self, managers):
        """Test that admin actions are logged (PRJ-SEC-003)."""
        auth = managers['auth']
        logger = managers['logger']
        pm = managers['product_manager']
        
        # Login as admin
        auth.login("admin", "admin123")
        username = auth.get_current_username()
        
        # Perform admin action
        product_id = pm.add_product("LOG001", "Logged Product", 10.00, "Cat", 50, user=username)
        pm.delete_product(product_id, user=username)
        
        # Verify actions were logged
        logs = logger.get_recent_logs(10)
        
        add_logs = [log for log in logs if 'ADD_PRODUCT' in log['action']]
        delete_logs = [log for log in logs if 'DELETE_PRODUCT' in log['action']]
        
        assert len(add_logs) >= 1
        assert len(delete_logs) >= 1

    def test_user_authentication_flow(self, managers):
        """Test complete user authentication flow."""
        auth = managers['auth']
        
        # Initial state - not authenticated
        assert not auth.is_authenticated()
        
        # Login
        success = auth.login("admin", "admin123")
        assert success is True
        assert auth.is_authenticated()
        assert auth.is_admin()
        
        # Logout
        auth.logout()
        assert not auth.is_authenticated()
        assert not auth.is_admin()


class TestCompleteWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_complete_inventory_workflow(self, temp_db):
        """Test complete workflow: add product, supplier, orders, reports."""
        # Initialize managers
        storage = StorageManager(temp_db)
        logger = LogManager(storage)
        pm = ProductManager(storage, logger)
        sm = SupplierManager(storage, logger)
        op = OrderProcessor(storage, logger, pm)
        
        # 1. Add supplier
        supplier_id = sm.add_supplier("Office Depot", "Sales Manager", "sales@depot.com")
        assert supplier_id > 0
        
        # 2. Add product
        product_id = pm.add_product("PEN001", "Blue Pen", 1.50, "Stationery", 200)
        assert product_id > 0
        
        # 3. Create purchase order (restock)
        po_id = op.create_purchase_order(product_id, supplier_id, 100, 0.75)
        assert po_id > 0
        
        # Verify stock increased to 300
        product = pm.get_product(product_id)
        assert product['stock'] == 300
        
        # 4. Create sales order
        so_id = op.create_sales_order(product_id, 50)
        assert so_id > 0
        
        # Verify stock decreased to 250
        product = pm.get_product(product_id)
        assert product['stock'] == 250
        
        # 5. Generate reports
        sales_report = op.get_sales_report()
        purchase_report = op.get_purchase_report()
        
        assert sales_report['total_orders'] >= 1
        assert purchase_report['total_orders'] >= 1
        assert sales_report['total_revenue'] >= 75.00  # 50 * 1.50
        assert purchase_report['total_cost'] >= 75.00  # 100 * 0.75

