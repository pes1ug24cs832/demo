"""
Unit tests for product_manager module.
Tests INV-F-001, INV-F-002, INV-F-003, INV-F-032.
"""

import pytest
import tempfile
import os
from src.product_manager import ProductManager
from src.storage import StorageManager
from src.logger import LogManager


class TestProductManager:
    """Test product manager."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def product_manager(self, temp_db):
        """Create product manager with temporary database."""
        storage = StorageManager(temp_db)
        logger = LogManager(storage)
        return ProductManager(storage, logger)

    def test_add_product_success(self, product_manager):
        """Test adding product successfully (INV-F-001)."""
        product_id = product_manager.add_product(
            sku="LAPTOP001",
            name="Gaming Laptop",
            price=1299.99,
            category="Electronics",
            stock=15,
            description="High-performance gaming laptop"
        )
        
        assert product_id is not None
        assert product_id > 0

    def test_add_product_duplicate_sku(self, product_manager):
        """Test adding product with duplicate SKU fails."""
        product_manager.add_product("LAPTOP001", "Laptop 1", 999.99, "Electronics", 10)
        
        # Try to add with same SKU
        result = product_manager.add_product("LAPTOP001", "Laptop 2", 899.99, "Electronics", 5)
        
        assert result is None

    def test_add_product_negative_price(self, product_manager):
        """Test adding product with negative price raises error."""
        with pytest.raises(ValueError):
            product_manager.add_product("TEST001", "Test", -10.00, "Cat", 10)

    def test_add_product_negative_stock(self, product_manager):
        """Test adding product with negative stock raises error."""
        with pytest.raises(ValueError):
            product_manager.add_product("TEST001", "Test", 10.00, "Cat", -5)

    def test_get_all_products(self, product_manager):
        """Test getting all products (INV-F-002)."""
        product_manager.add_product("PROD001", "Product 1", 10.00, "Cat1", 50)
        product_manager.add_product("PROD002", "Product 2", 20.00, "Cat2", 30)
        
        products = product_manager.get_all_products()
        
        assert len(products) >= 2

    def test_get_product(self, product_manager):
        """Test getting single product by ID."""
        product_id = product_manager.add_product("PROD001", "Product 1", 10.00, "Cat1", 50)
        
        product = product_manager.get_product(product_id)
        
        assert product is not None
        assert product['sku'] == "PROD001"
        assert product['name'] == "Product 1"

    def test_search_products(self, product_manager):
        """Test searching products (INV-F-002)."""
        product_manager.add_product("LAPTOP001", "Gaming Laptop", 1299.99, "Electronics", 10)
        product_manager.add_product("LAPTOP002", "Business Laptop", 999.99, "Electronics", 15)
        product_manager.add_product("CHAIR001", "Office Chair", 199.99, "Furniture", 20)
        
        # Search by keyword
        results = product_manager.search_products("Laptop")
        assert len(results) == 2
        
        # Search by category
        results = product_manager.search_products("Electronics")
        assert len(results) == 2

    def test_update_product_success(self, product_manager):
        """Test updating product (INV-F-003)."""
        product_id = product_manager.add_product("PROD001", "Old Name", 10.00, "Cat1", 50)
        
        success = product_manager.update_product(
            product_id,
            name="New Name",
            price=15.00,
            stock=60
        )
        
        assert success is True
        
        product = product_manager.get_product(product_id)
        assert product['name'] == "New Name"
        assert product['price'] == 15.00
        assert product['stock'] == 60

    def test_update_product_not_found(self, product_manager):
        """Test updating non-existent product fails."""
        success = product_manager.update_product(99999, name="Test")
        
        assert success is False

    def test_update_product_negative_price(self, product_manager):
        """Test updating product with negative price raises error."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 50)
        
        with pytest.raises(ValueError):
            product_manager.update_product(product_id, price=-5.00)

    def test_delete_product_success(self, product_manager):
        """Test deleting product."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 50)
        
        success = product_manager.delete_product(product_id)
        
        assert success is True
        
        product = product_manager.get_product(product_id)
        assert product is None

    def test_delete_product_not_found(self, product_manager):
        """Test deleting non-existent product."""
        success = product_manager.delete_product(99999)
        
        assert success is False

    def test_get_low_stock_products(self, product_manager):
        """Test getting low stock products (INV-F-032)."""
        product_manager.add_product("LOW001", "Low Stock Item", 10.00, "Cat", 2)
        product_manager.add_product("GOOD001", "Good Stock Item", 20.00, "Cat", 100)
        
        low_stock = product_manager.get_low_stock_products(threshold=5)
        
        assert len(low_stock) >= 1
        assert all(p['stock'] <= 5 for p in low_stock)

    def test_check_stock_availability_sufficient(self, product_manager):
        """Test checking stock availability with sufficient stock."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 100)
        
        available = product_manager.check_stock_availability(product_id, 50)
        
        assert available is True

    def test_check_stock_availability_insufficient(self, product_manager):
        """Test checking stock availability with insufficient stock."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 10)
        
        available = product_manager.check_stock_availability(product_id, 50)
        
        assert available is False

    def test_adjust_stock_increase(self, product_manager):
        """Test increasing stock."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 50)
        
        success = product_manager.adjust_stock(product_id, 20)
        
        assert success is True
        
        product = product_manager.get_product(product_id)
        assert product['stock'] == 70

    def test_adjust_stock_decrease(self, product_manager):
        """Test decreasing stock."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 50)
        
        success = product_manager.adjust_stock(product_id, -10)
        
        assert success is True
        
        product = product_manager.get_product(product_id)
        assert product['stock'] == 40

    def test_adjust_stock_insufficient(self, product_manager):
        """Test adjusting stock below zero raises error."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 10)
        
        with pytest.raises(ValueError):
            product_manager.adjust_stock(product_id, -20)
