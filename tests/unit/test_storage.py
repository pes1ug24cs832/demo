"""
Unit tests for storage module.
Tests database operations and persistence (INV-NF-002).
"""

import pytest
import tempfile
import os
from src.storage import StorageManager


class TestStorageManager:
    """Test storage manager."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def storage(self, temp_db):
        """Create storage manager with temporary database."""
        return StorageManager(temp_db)

    def test_database_initialization(self, storage):
        """Test database tables are created."""
        conn = storage.get_connection()
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'users' in tables
        assert 'products' in tables
        assert 'suppliers' in tables
        assert 'sales_orders' in tables
        assert 'purchase_orders' in tables
        assert 'logs' in tables
        
        conn.close()

    def test_admin_user_seeded(self, storage):
        """Test admin user is seeded."""
        user = storage.get_user_by_username("admin")
        
        assert user is not None
        assert user['username'] == "admin"
        assert user['role'] == "admin"

    def test_add_product(self, storage):
        """Test adding product (INV-F-001)."""
        product_id = storage.add_product(
            sku="TEST001",
            name="Test Product",
            price=99.99,
            category="Test Category",
            stock=100,
            description="Test description"
        )
        
        assert product_id is not None
        assert product_id > 0

    def test_get_product_by_id(self, storage):
        """Test retrieving product by ID."""
        product_id = storage.add_product("TEST001", "Test Product", 99.99, "Test", 100)
        
        product = storage.get_product_by_id(product_id)
        
        assert product is not None
        assert product['sku'] == "TEST001"
        assert product['name'] == "Test Product"
        assert product['price'] == 99.99
        assert product['stock'] == 100

    def test_get_product_by_sku(self, storage):
        """Test retrieving product by SKU."""
        storage.add_product("TEST001", "Test Product", 99.99, "Test", 100)
        
        product = storage.get_product_by_sku("TEST001")
        
        assert product is not None
        assert product['sku'] == "TEST001"

    def test_get_all_products(self, storage):
        """Test getting all products (INV-F-002)."""
        storage.add_product("TEST001", "Product 1", 10.00, "Cat1", 50)
        storage.add_product("TEST002", "Product 2", 20.00, "Cat2", 30)
        
        products = storage.get_all_products()
        
        assert len(products) >= 2

    def test_search_products(self, storage):
        """Test searching products (INV-F-002)."""
        storage.add_product("TEST001", "Laptop Computer", 999.99, "Electronics", 10)
        storage.add_product("TEST002", "Desktop Computer", 799.99, "Electronics", 5)
        storage.add_product("TEST003", "Office Chair", 199.99, "Furniture", 20)
        
        # Search by name
        results = storage.search_products("Computer")
        assert len(results) == 2
        
        # Search by category
        results = storage.search_products("Electronics")
        assert len(results) == 2

    def test_update_product(self, storage):
        """Test updating product (INV-F-003)."""
        product_id = storage.add_product("TEST001", "Old Name", 10.00, "Cat1", 50)
        
        success = storage.update_product(product_id, name="New Name", price=15.00)
        
        assert success is True
        
        product = storage.get_product_by_id(product_id)
        assert product['name'] == "New Name"
        assert product['price'] == 15.00

    def test_delete_product(self, storage):
        """Test deleting product."""
        product_id = storage.add_product("TEST001", "Test", 10.00, "Cat1", 50)
        
        success = storage.delete_product(product_id)
        assert success is True
        
        product = storage.get_product_by_id(product_id)
        assert product is None

    def test_get_low_stock_products(self, storage):
        """Test getting low stock products (INV-F-032)."""
        storage.add_product("TEST001", "Low Stock", 10.00, "Cat1", 3)
        storage.add_product("TEST002", "Good Stock", 20.00, "Cat2", 100)
        
        low_stock = storage.get_low_stock_products(threshold=5)
        
        assert len(low_stock) >= 1
        assert all(p['stock'] <= 5 for p in low_stock)

    def test_add_supplier(self, storage):
        """Test adding supplier (INV-F-020)."""
        supplier_id = storage.add_supplier(
            name="Test Supplier",
            contact_person="John Doe",
            email="john@test.com",
            phone="123-456-7890",
            address="123 Test St"
        )
        
        assert supplier_id is not None
        assert supplier_id > 0

    def test_get_all_suppliers(self, storage):
        """Test getting all suppliers (INV-F-021)."""
        storage.add_supplier("Supplier 1", "Contact 1", "email1@test.com")
        storage.add_supplier("Supplier 2", "Contact 2", "email2@test.com")
        
        suppliers = storage.get_all_suppliers()
        
        assert len(suppliers) >= 2

    def test_create_sales_order(self, storage):
        """Test creating sales order (INV-F-010)."""
        product_id = storage.add_product("TEST001", "Product", 10.00, "Cat", 100)
        
        order_id = storage.create_sales_order(product_id, 5, 50.00)
        
        assert order_id is not None
        assert order_id > 0

    def test_create_purchase_order(self, storage):
        """Test creating purchase order (INV-F-012)."""
        product_id = storage.add_product("TEST001", "Product", 10.00, "Cat", 100)
        supplier_id = storage.add_supplier("Supplier", "Contact", "email@test.com")
        
        order_id = storage.create_purchase_order(product_id, supplier_id, 10, 8.00, 80.00)
        
        assert order_id is not None
        assert order_id > 0

    def test_get_sales_orders(self, storage):
        """Test getting sales orders (INV-F-031)."""
        product_id = storage.add_product("TEST001", "Product", 10.00, "Cat", 100)
        storage.create_sales_order(product_id, 5, 50.00)
        
        orders = storage.get_sales_orders()
        
        assert len(orders) >= 1

    def test_add_log(self, storage):
        """Test adding log entry (PRJ-SEC-003)."""
        log_id = storage.add_log("admin", "TEST_ACTION", "Test details")
        
        assert log_id is not None
        assert log_id > 0

    def test_get_logs(self, storage):
        """Test getting log entries."""
        storage.add_log("admin", "ACTION1", "Details 1")
        storage.add_log("admin", "ACTION2", "Details 2")
        
        logs = storage.get_logs(10)
        
        assert len(logs) >= 2

    def test_get_inventory_summary(self, storage):
        """Test inventory summary report (INV-F-030)."""
        storage.add_product("TEST001", "Product 1", 10.00, "Electronics", 50)
        storage.add_product("TEST002", "Product 2", 20.00, "Electronics", 30)
        storage.add_product("TEST003", "Product 3", 15.00, "Furniture", 40)
        
        summary = storage.get_inventory_summary()
        
        assert 'total_products' in summary
        assert 'total_stock' in summary
        assert 'by_category' in summary
        assert summary['total_products'] >= 3
