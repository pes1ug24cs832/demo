"""
Additional unit tests for response time validation.
Tests INV-NF-001 (Response time ≤ 2s).
"""

import pytest
import time
import tempfile
import os
from src.storage import StorageManager
from src.product_manager import ProductManager
from src.logger import LogManager


class TestResponseTime:
    """Test response time requirements (INV-NF-001)."""

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

    def test_add_product_response_time(self, product_manager):
        """Test add product response time ≤ 2s (INV-NF-001)."""
        start_time = time.time()
        
        product_manager.add_product("PERF001", "Performance Test", 10.00, "Test", 50)
        
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 2.0, f"Add product took {elapsed_time:.3f}s (should be < 2s)"

    def test_search_products_response_time(self, product_manager):
        """Test search products response time ≤ 2s (INV-NF-001)."""
        # Add some products first
        for i in range(50):
            product_manager.add_product(f"PROD{i:03d}", f"Product {i}", 10.00, "Category", 50)
        
        start_time = time.time()
        
        product_manager.search_products("Product")
        
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 2.0, f"Search products took {elapsed_time:.3f}s (should be < 2s)"

    def test_get_all_products_response_time(self, product_manager):
        """Test get all products response time ≤ 2s (INV-NF-001)."""
        # Add products
        for i in range(100):
            product_manager.add_product(f"PROD{i:03d}", f"Product {i}", 10.00, "Category", 50)
        
        start_time = time.time()
        
        product_manager.get_all_products()
        
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 2.0, f"Get all products took {elapsed_time:.3f}s (should be < 2s)"

    def test_update_product_response_time(self, product_manager):
        """Test update product response time ≤ 2s (INV-NF-001)."""
        product_id = product_manager.add_product("PERF001", "Test", 10.00, "Cat", 50)
        
        start_time = time.time()
        
        product_manager.update_product(product_id, name="Updated Name", price=15.00)
        
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 2.0, f"Update product took {elapsed_time:.3f}s (should be < 2s)"

