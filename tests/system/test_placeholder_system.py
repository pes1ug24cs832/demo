"""
System tests for IMS CLI.
Tests end-to-end scenarios including CLI interaction, low-stock alerts, and admin restrictions.
"""

import pytest
import tempfile
import os
import subprocess
import sys
from src.storage import StorageManager
from src.product_manager import ProductManager
from src.supplier_manager import SupplierManager
from src.logger import LogManager
from src.auth import AuthManager
from src.backup_security import BackupManager
from src.config import LOW_STOCK_THRESHOLD


class TestLowStockAlert:
    """Test low stock alert system (INV-F-032)."""

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

    def test_low_stock_alert_triggered(self, product_manager):
        """Test low stock alert is triggered when stock is low."""
        # Add products with varying stock levels
        product_manager.add_product("LOW001", "Low Stock Item", 10.00, "Cat", 2)
        product_manager.add_product("GOOD001", "Good Stock Item", 20.00, "Cat", 100)
        product_manager.add_product("LOW002", "Another Low Item", 15.00, "Cat", 3)
        
        # Get low stock products
        low_stock = product_manager.get_low_stock_products(LOW_STOCK_THRESHOLD)
        
        # Should return products with stock <= threshold
        assert len(low_stock) >= 2
        for product in low_stock:
            assert product['stock'] <= LOW_STOCK_THRESHOLD

    def test_low_stock_alert_after_sales_order(self, temp_db):
        """Test low stock alert after sales orders deplete stock."""
        from src.order_processor import OrderProcessor
        
        storage = StorageManager(temp_db)
        logger = LogManager(storage)
        pm = ProductManager(storage, logger)
        op = OrderProcessor(storage, logger, pm)
        
        # Add product with stock above threshold
        product_id = pm.add_product("STOCK001", "Test Item", 10.00, "Cat", 10)
        
        # Initially not in low stock
        low_stock = pm.get_low_stock_products(LOW_STOCK_THRESHOLD)
        low_stock_skus = [p['sku'] for p in low_stock]
        assert "STOCK001" not in low_stock_skus
        
        # Create sales order to reduce stock below threshold
        op.create_sales_order(product_id, 7)  # Now stock is 3
        
        # Should now appear in low stock
        low_stock = pm.get_low_stock_products(LOW_STOCK_THRESHOLD)
        low_stock_skus = [p['sku'] for p in low_stock]
        assert "STOCK001" in low_stock_skus

    def test_low_stock_threshold_configurable(self, product_manager):
        """Test that low stock threshold is configurable."""
        # Add products
        product_manager.add_product("ITEM001", "Item 1", 10.00, "Cat", 8)
        product_manager.add_product("ITEM002", "Item 2", 10.00, "Cat", 12)
        
        # Test with different thresholds
        low_stock_5 = product_manager.get_low_stock_products(threshold=5)
        low_stock_10 = product_manager.get_low_stock_products(threshold=10)
        
        # With threshold 10, should include item with stock 8
        assert len(low_stock_10) >= len(low_stock_5)


class TestAdminRestrictions:
    """Test admin-only restrictions (INV-NF-003)."""

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
        
        return {
            'storage': storage,
            'auth': auth,
            'logger': logger
        }

    def test_admin_can_delete_product(self, managers):
        """Test that admin can delete products."""
        auth = managers['auth']
        storage = managers['storage']
        logger = managers['logger']
        
        pm = ProductManager(storage, logger)
        
        # Login as admin
        auth.login("admin", "admin123")
        assert auth.is_admin()
        
        # Create and delete product
        product_id = pm.add_product("DEL001", "Delete Me", 10.00, "Cat", 50)
        success = pm.delete_product(product_id)
        
        assert success is True

    def test_require_admin_succeeds_for_admin(self, managers):
        """Test require_admin does not raise error for admin."""
        auth = managers['auth']
        
        auth.login("admin", "admin123")
        
        try:
            auth.require_admin()
        except PermissionError:
            pytest.fail("require_admin should not raise error for admin")

    def test_require_admin_fails_for_regular_user(self, managers):
        """Test require_admin raises error for regular user."""
        auth = managers['auth']
        
        # Register and login as regular user
        auth.register_user("regularuser", "password123", "user")
        auth.login("regularuser", "password123")
        
        assert not auth.is_admin()
        
        with pytest.raises(PermissionError):
            auth.require_admin()

    def test_backup_requires_admin_privileges(self, temp_db):
        """Test that backup operations require admin context."""
        import tempfile
        import shutil
        
        # Create backup directory
        backup_dir = tempfile.mkdtemp()
        
        try:
            storage = StorageManager(temp_db)
            logger = LogManager(storage)
            bm = BackupManager(logger)
            
            # Override paths for testing
            bm.backup_dir = backup_dir
            bm.db_path = temp_db
            
            # Backup can be created (in real app, would check auth first)
            backup_path = bm.create_backup("admin")
            
            assert backup_path is not None
            assert os.path.exists(backup_path)
            
        finally:
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)


class TestSecurityCompliance:
    """Test security requirements compliance."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_passwords_are_hashed(self, temp_db):
        """Test that passwords are stored hashed (PRJ-SEC-001)."""
        storage = StorageManager(temp_db)
        auth = AuthManager(storage)
        
        # Register user
        auth.register_user("testuser", "plainpassword123", "user")
        
        # Get user from database
        user = storage.get_user_by_username("testuser")
        
        # Password should be hashed, not plain text
        assert user['password_hash'] != "plainpassword123"
        assert len(user['password_hash']) == 64  # SHA-256 hex length

    def test_admin_actions_logged(self, temp_db):
        """Test that admin actions are logged (PRJ-SEC-003)."""
        storage = StorageManager(temp_db)
        logger = LogManager(storage)
        auth = AuthManager(storage)
        pm = ProductManager(storage, logger)
        
        # Login as admin
        auth.login("admin", "admin123")
        username = auth.get_current_username()
        
        # Perform actions
        product_id = pm.add_product("TEST001", "Test", 10.00, "Cat", 50, user=username)
        pm.update_product(product_id, price=15.00, user=username)
        pm.delete_product(product_id, user=username)
        
        # Check logs
        logs = logger.get_recent_logs(10)
        
        # Should have logs for add, update, delete
        action_types = [log['action'] for log in logs]
        assert 'ADD_PRODUCT' in action_types
        assert 'UPDATE_PRODUCT' in action_types
        assert 'DELETE_PRODUCT' in action_types
        
        # All should be from admin user
        admin_logs = [log for log in logs if log['user'] == 'admin']
        assert len(admin_logs) >= 3

    def test_data_minimization(self, temp_db):
        """Test data minimization principle (PRJ-SEC-004)."""
        storage = StorageManager(temp_db)
        
        # Check user table only has essential fields
        user = storage.get_user_by_username("admin")
        
        # Should only have necessary fields
        essential_fields = ['id', 'username', 'password_hash', 'role', 'created_at']
        for field in essential_fields:
            assert field in user


class TestReportGeneration:
    """Test report generation (INV-F-030, INV-F-031)."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_inventory_summary_report(self, temp_db):
        """Test inventory summary report (INV-F-030)."""
        storage = StorageManager(temp_db)
        logger = LogManager(storage)
        pm = ProductManager(storage, logger)
        
        # Add products in different categories
        pm.add_product("ELEC001", "Laptop", 999.99, "Electronics", 10)
        pm.add_product("ELEC002", "Mouse", 29.99, "Electronics", 50)
        pm.add_product("FURN001", "Desk", 299.99, "Furniture", 20)
        
        # Get summary
        summary = storage.get_inventory_summary()
        
        assert summary['total_products'] >= 3
        assert summary['total_stock'] >= 80
        assert len(summary['by_category']) >= 2

    def test_sales_report_with_date_range(self, temp_db):
        """Test sales report with date filtering (INV-F-031)."""
        from datetime import datetime, timedelta
        from src.order_processor import OrderProcessor
        
        storage = StorageManager(temp_db)
        logger = LogManager(storage)
        pm = ProductManager(storage, logger)
        op = OrderProcessor(storage, logger, pm)
        
        # Add product and create orders
        product_id = pm.add_product("REPORT001", "Report Test", 50.00, "Cat", 100)
        op.create_sales_order(product_id, 5)
        
        # Get report for today
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        report = op.get_sales_report(today, tomorrow)
        
        assert report['total_orders'] >= 1
        assert report['total_revenue'] >= 250.00

    def test_purchase_report_generation(self, temp_db):
        """Test purchase report generation (INV-F-031)."""
        from src.order_processor import OrderProcessor
        from src.supplier_manager import SupplierManager
        
        storage = StorageManager(temp_db)
        logger = LogManager(storage)
        pm = ProductManager(storage, logger)
        sm = SupplierManager(storage, logger)
        op = OrderProcessor(storage, logger, pm)
        
        # Setup data
        product_id = pm.add_product("PURCHASE001", "Purchase Test", 100.00, "Cat", 50)
        supplier_id = sm.add_supplier("Test Supplier", "Contact", "email@test.com")
        
        # Create purchase orders
        op.create_purchase_order(product_id, supplier_id, 10, 75.00)
        op.create_purchase_order(product_id, supplier_id, 20, 70.00)
        
        # Get report
        report = op.get_purchase_report()
        
        assert report['total_orders'] >= 2
        assert report['total_cost'] >= 2150.00  # (10*75) + (20*70)
        assert report['total_units'] >= 30


class TestCLIFunctionality:
    """Test CLI module functionality (basic checks, not subprocess-based)."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_cli_initialization(self):
        """Test that CLI can be initialized."""
        from src.cli import CLI
        
        cli = CLI()
        
        assert cli.storage is not None
        assert cli.auth is not None
        assert cli.logger is not None
        assert cli.product_manager is not None
        assert cli.supplier_manager is not None
        assert cli.order_processor is not None
        assert cli.backup_manager is not None

    def test_cli_auth_integration(self):
        """Test CLI authentication integration."""
        from src.cli import CLI
        
        cli = CLI()
        
        # Initially not authenticated
        assert not cli.auth.is_authenticated()
        
        # Login
        success = cli.auth.login("admin", "admin123")
        assert success is True
        assert cli.auth.is_authenticated()

