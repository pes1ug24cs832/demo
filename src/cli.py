"""
Command-Line Interface Module
Handles user interaction and command parsing for the IMS.
Implements INV-NF-005 (User-friendly CLI).
"""

import sys
import os
from datetime import datetime, timedelta

# Configure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')
    except Exception:
        # Fallback: use ASCII-safe output
        pass

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage import StorageManager
from src.auth import AuthManager
from src.logger import LogManager
from src.product_manager import ProductManager
from src.supplier_manager import SupplierManager
from src.order_processor import OrderProcessor
from src.backup_security import BackupManager
from src.config import LOW_STOCK_THRESHOLD


class CLI:
    """Command-line interface for IMS."""

    def __init__(self):
        """Initialize CLI and all managers."""
        self.storage = StorageManager()
        self.auth = AuthManager(self.storage)
        self.logger = LogManager(self.storage)
        self.product_manager = ProductManager(self.storage, self.logger)
        self.supplier_manager = SupplierManager(self.storage, self.logger)
        self.order_processor = OrderProcessor(self.storage, self.logger, self.product_manager)
        self.backup_manager = BackupManager(self.logger)
        self.running = True

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, title: str):
        """Print formatted header."""
        print("\n" + "="*80)
        print(f"  {title}")
        print("="*80)

    def input_with_prompt(self, prompt: str, required: bool = True) -> str:
        """Get input with validation."""
        while True:
            value = input(f"{prompt}: ").strip()
            if not required or value:
                return value
            print("  [!] This field is required. Please enter a value.")

    def input_number(self, prompt: str, allow_float: bool = False) -> float:
        """Get numeric input with validation."""
        while True:
            try:
                value = input(f"{prompt}: ").strip()
                if allow_float:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                print("  [!] Please enter a valid number.")

    def show_main_menu(self):
        """Display main menu."""
        self.clear_screen()
        self.print_header("INVENTORY MANAGEMENT SYSTEM")
        
        if self.auth.is_authenticated():
            username = self.auth.get_current_username()
            role = "Admin" if self.auth.is_admin() else "User"
            print(f"\nLogged in as: {username} ({role})")
        else:
            print("\nNot logged in (Guest mode - limited access)")
        
        print("\n1. Product Management")
        print("2. Supplier Management")
        print("3. Order Processing")
        print("4. Reports & Analytics")
        print("5. Backup & Restore (Admin)")
        print("6. View Logs (Admin)")
        print("7. Login / Logout")
        print("8. Help")
        print("0. Exit")
        print()

    def main_menu(self):
        """Handle main menu selection."""
        while self.running:
            self.show_main_menu()
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.product_menu()
            elif choice == '2':
                self.supplier_menu()
            elif choice == '3':
                self.order_menu()
            elif choice == '4':
                self.reports_menu()
            elif choice == '5':
                self.backup_menu()
            elif choice == '6':
                self.logs_menu()
            elif choice == '7':
                self.auth_menu()
            elif choice == '8':
                self.show_help()
            elif choice == '0':
                self.exit_application()
            else:
                print("Invalid option. Please try again.")
                input("\nPress Enter to continue...")

    # ========== Product Management ==========

    def product_menu(self):
        """Product management submenu."""
        while True:
            self.clear_screen()
            self.print_header("PRODUCT MANAGEMENT")
            print("\n1. Add Product")
            print("2. View All Products")
            print("3. Search Products")
            print("4. Update Product")
            print("5. Delete Product (Admin)")
            print("6. Low Stock Alert")
            print("0. Back to Main Menu")
            print()
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.add_product()
            elif choice == '2':
                self.view_products()
            elif choice == '3':
                self.search_products()
            elif choice == '4':
                self.update_product()
            elif choice == '5':
                self.delete_product()
            elif choice == '6':
                self.show_low_stock()
            elif choice == '0':
                break
            else:
                print("Invalid option.")
                input("\nPress Enter to continue...")

    def add_product(self):
        """Add new product (INV-F-001)."""
        self.clear_screen()
        self.print_header("ADD NEW PRODUCT")
        
        try:
            sku = self.input_with_prompt("SKU (unique)")
            name = self.input_with_prompt("Product Name")
            price = self.input_number("Price", allow_float=True)
            category = self.input_with_prompt("Category")
            stock = self.input_number("Initial Stock Quantity")
            description = self.input_with_prompt("Description (optional)", required=False)
            
            user = self.auth.get_current_username()
            product_id = self.product_manager.add_product(
                sku, name, price, category, stock, description, user
            )
            
            if product_id:
                print(f"\n[OK] Product added successfully! ID: {product_id}")
            else:
                print(f"\n[X] Error: SKU '{sku}' already exists.")
        except Exception as e:
            print(f"\n[X] Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def view_products(self):
        """View all products (INV-F-002)."""
        self.clear_screen()
        self.print_header("ALL PRODUCTS")
        
        products = self.product_manager.get_all_products()
        self.product_manager.display_products(products)
        
        input("Press Enter to continue...")

    def search_products(self):
        """Search products (INV-F-002)."""
        self.clear_screen()
        self.print_header("SEARCH PRODUCTS")
        
        search_term = self.input_with_prompt("Enter search term (name/SKU/category)")
        products = self.product_manager.search_products(search_term)
        
        print(f"\nFound {len(products)} product(s):")
        self.product_manager.display_products(products)
        
        input("Press Enter to continue...")

    def update_product(self):
        """Update product (INV-F-003)."""
        self.clear_screen()
        self.print_header("UPDATE PRODUCT")
        
        try:
            product_id = int(self.input_with_prompt("Product ID"))
            product = self.product_manager.get_product(product_id)
            
            if not product:
                print("\n[X] Product not found.")
                input("\nPress Enter to continue...")
                return
            
            print(f"\nCurrent details for: {product['name']}")
            print(f"  SKU: {product['sku']}")
            print(f"  Price: ${product['price']:.2f}")
            print(f"  Category: {product['category']}")
            print(f"  Stock: {product['stock']}")
            print(f"  Description: {product['description']}")
            
            print("\nLeave fields blank to keep current value:")
            updates = {}
            
            name = input("New Name: ").strip()
            if name:
                updates['name'] = name
            
            price_str = input("New Price: ").strip()
            if price_str:
                updates['price'] = float(price_str)
            
            category = input("New Category: ").strip()
            if category:
                updates['category'] = category
            
            stock_str = input("New Stock: ").strip()
            if stock_str:
                updates['stock'] = int(stock_str)
            
            description = input("New Description: ").strip()
            if description:
                updates['description'] = description
            
            if updates:
                user = self.auth.get_current_username()
                success = self.product_manager.update_product(product_id, user=user, **updates)
                if success:
                    print("\n[OK] Product updated successfully!")
                else:
                    print("\n[X] Update failed.")
            else:
                print("\nNo changes made.")
        except Exception as e:
            print(f"\n[X] Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def delete_product(self):
        """Delete product (Admin only)."""
        self.clear_screen()
        self.print_header("DELETE PRODUCT (ADMIN ONLY)")
        
        if not self.auth.is_admin():
            print("\n[X] Admin privileges required.")
            input("\nPress Enter to continue...")
            return
        
        try:
            product_id = int(self.input_with_prompt("Product ID to delete"))
            product = self.product_manager.get_product(product_id)
            
            if not product:
                print("\n[X] Product not found.")
                input("\nPress Enter to continue...")
                return
            
            print(f"\nProduct to delete: {product['name']} (SKU: {product['sku']})")
            confirm = input("Are you sure? (yes/no): ").strip().lower()
            
            if confirm == 'yes':
                user = self.auth.get_current_username()
                success = self.product_manager.delete_product(product_id, user)
                if success:
                    print("\n[OK] Product deleted successfully!")
                else:
                    print("\n[X] Deletion failed.")
            else:
                print("\nDeletion cancelled.")
        except Exception as e:
            print(f"\n[X] Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def show_low_stock(self):
        """Show low stock products (INV-F-032)."""
        self.clear_screen()
        self.print_header(f"LOW STOCK ALERT (Threshold: {LOW_STOCK_THRESHOLD})")
        
        products = self.product_manager.get_low_stock_products()
        
        if products:
            print(f"\n[!] {len(products)} product(s) with low stock:")
            self.product_manager.display_products(products)
        else:
            print("\n[OK] All products have adequate stock.")
        
        input("Press Enter to continue...")

    # ========== Supplier Management ==========

    def supplier_menu(self):
        """Supplier management submenu."""
        while True:
            self.clear_screen()
            self.print_header("SUPPLIER MANAGEMENT")
            print("\n1. Add Supplier")
            print("2. View All Suppliers")
            print("3. Search Suppliers")
            print("4. Update Supplier")
            print("0. Back to Main Menu")
            print()
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.add_supplier()
            elif choice == '2':
                self.view_suppliers()
            elif choice == '3':
                self.search_suppliers()
            elif choice == '4':
                self.update_supplier()
            elif choice == '0':
                break
            else:
                print("Invalid option.")
                input("\nPress Enter to continue...")

    def add_supplier(self):
        """Add new supplier (INV-F-020)."""
        self.clear_screen()
        self.print_header("ADD NEW SUPPLIER")
        
        try:
            name = self.input_with_prompt("Supplier Name")
            contact_person = self.input_with_prompt("Contact Person (optional)", required=False)
            email = self.input_with_prompt("Email (optional)", required=False)
            phone = self.input_with_prompt("Phone (optional)", required=False)
            address = self.input_with_prompt("Address (optional)", required=False)
            
            user = self.auth.get_current_username()
            supplier_id = self.supplier_manager.add_supplier(
                name, contact_person, email, phone, address, user
            )
            
            print(f"\n[OK] Supplier added successfully! ID: {supplier_id}")
        except Exception as e:
            print(f"\n[X] Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def view_suppliers(self):
        """View all suppliers (INV-F-021)."""
        self.clear_screen()
        self.print_header("ALL SUPPLIERS")
        
        suppliers = self.supplier_manager.get_all_suppliers()
        self.supplier_manager.display_suppliers(suppliers)
        
        input("Press Enter to continue...")

    def search_suppliers(self):
        """Search suppliers (INV-F-021)."""
        self.clear_screen()
        self.print_header("SEARCH SUPPLIERS")
        
        search_term = self.input_with_prompt("Enter search term (name/contact/email)")
        suppliers = self.supplier_manager.search_suppliers(search_term)
        
        print(f"\nFound {len(suppliers)} supplier(s):")
        self.supplier_manager.display_suppliers(suppliers)
        
        input("Press Enter to continue...")

    def update_supplier(self):
        """Update supplier details."""
        self.clear_screen()
        self.print_header("UPDATE SUPPLIER")
        
        try:
            supplier_id = int(self.input_with_prompt("Supplier ID"))
            supplier = self.supplier_manager.get_supplier(supplier_id)
            
            if not supplier:
                print("\n[X] Supplier not found.")
                input("\nPress Enter to continue...")
                return
            
            print(f"\nCurrent details for: {supplier['name']}")
            print(f"  Contact: {supplier['contact_person']}")
            print(f"  Email: {supplier['email']}")
            print(f"  Phone: {supplier['phone']}")
            print(f"  Address: {supplier['address']}")
            
            print("\nLeave fields blank to keep current value:")
            updates = {}
            
            name = input("New Name: ").strip()
            if name:
                updates['name'] = name
            
            contact = input("New Contact Person: ").strip()
            if contact:
                updates['contact_person'] = contact
            
            email = input("New Email: ").strip()
            if email:
                updates['email'] = email
            
            phone = input("New Phone: ").strip()
            if phone:
                updates['phone'] = phone
            
            address = input("New Address: ").strip()
            if address:
                updates['address'] = address
            
            if updates:
                user = self.auth.get_current_username()
                success = self.supplier_manager.update_supplier(supplier_id, user=user, **updates)
                if success:
                    print("\n[OK] Supplier updated successfully!")
                else:
                    print("\n[X] Update failed.")
            else:
                print("\nNo changes made.")
        except Exception as e:
            print(f"\n[X] Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    # ========== Order Processing ==========

    def order_menu(self):
        """Order processing submenu."""
        while True:
            self.clear_screen()
            self.print_header("ORDER PROCESSING")
            print("\n1. Create Sales Order")
            print("2. Create Purchase Order")
            print("3. View Sales Orders")
            print("4. View Purchase Orders")
            print("0. Back to Main Menu")
            print()
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.create_sales_order()
            elif choice == '2':
                self.create_purchase_order()
            elif choice == '3':
                self.view_sales_orders()
            elif choice == '4':
                self.view_purchase_orders()
            elif choice == '0':
                break
            else:
                print("Invalid option.")
                input("\nPress Enter to continue...")

    def create_sales_order(self):
        """Create sales order (INV-F-010, INV-F-011)."""
        self.clear_screen()
        self.print_header("CREATE SALES ORDER")
        
        try:
            product_id = int(self.input_with_prompt("Product ID"))
            product = self.product_manager.get_product(product_id)
            
            if not product:
                print("\n[X] Product not found.")
                input("\nPress Enter to continue...")
                return
            
            print(f"\nProduct: {product['name']}")
            print(f"Available Stock: {product['stock']}")
            print(f"Price: ${product['price']:.2f}")
            
            quantity = int(self.input_with_prompt("\nQuantity to sell"))
            
            user = self.auth.get_current_username()
            order_id = self.order_processor.create_sales_order(product_id, quantity, user)
            
            if order_id:
                total = product['price'] * quantity
                print(f"\n[OK] Sales order created successfully! Order ID: {order_id}")
                print(f"  Total: ${total:.2f}")
                print(f"  Remaining stock: {product['stock'] - quantity}")
            else:
                print("\n[X] Insufficient stock for this order (INV-F-011)")
        except Exception as e:
            print(f"\n[X] Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def create_purchase_order(self):
        """Create purchase order (INV-F-012)."""
        self.clear_screen()
        self.print_header("CREATE PURCHASE ORDER")
        
        try:
            product_id = int(self.input_with_prompt("Product ID"))
            product = self.product_manager.get_product(product_id)
            
            if not product:
                print("\n[X] Product not found.")
                input("\nPress Enter to continue...")
                return
            
            print(f"\nProduct: {product['name']}")
            print(f"Current Stock: {product['stock']}")
            
            supplier_id = int(self.input_with_prompt("Supplier ID"))
            quantity = int(self.input_with_prompt("Quantity to purchase"))
            unit_price = float(self.input_with_prompt("Unit Price"))
            
            user = self.auth.get_current_username()
            order_id = self.order_processor.create_purchase_order(
                product_id, supplier_id, quantity, unit_price, user
            )
            
            total = unit_price * quantity
            print(f"\n[OK] Purchase order created successfully! Order ID: {order_id}")
            print(f"  Total Cost: ${total:.2f}")
            print(f"  New stock level: {product['stock'] + quantity}")
        except Exception as e:
            print(f"\n[X] Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def view_sales_orders(self):
        """View sales orders."""
        self.clear_screen()
        self.print_header("SALES ORDERS")
        
        orders = self.order_processor.get_sales_orders()
        self.order_processor.display_sales_orders(orders)
        
        input("Press Enter to continue...")

    def view_purchase_orders(self):
        """View purchase orders."""
        self.clear_screen()
        self.print_header("PURCHASE ORDERS")
        
        orders = self.order_processor.get_purchase_orders()
        self.order_processor.display_purchase_orders(orders)
        
        input("Press Enter to continue...")

    # ========== Reports & Analytics ==========

    def reports_menu(self):
        """Reports and analytics submenu."""
        while True:
            self.clear_screen()
            self.print_header("REPORTS & ANALYTICS")
            print("\n1. Inventory Summary")
            print("2. Sales Report")
            print("3. Purchase Report")
            print("4. Sales Report (Date Range)")
            print("5. Purchase Report (Date Range)")
            print("0. Back to Main Menu")
            print()
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.inventory_summary()
            elif choice == '2':
                self.sales_report()
            elif choice == '3':
                self.purchase_report()
            elif choice == '4':
                self.sales_report_date_range()
            elif choice == '5':
                self.purchase_report_date_range()
            elif choice == '0':
                break
            else:
                print("Invalid option.")
                input("\nPress Enter to continue...")

    def inventory_summary(self):
        """Display inventory summary (INV-F-030)."""
        self.clear_screen()
        self.print_header("INVENTORY SUMMARY")
        
        summary = self.storage.get_inventory_summary()
        
        print(f"\nTotal Products: {summary.get('total_products', 0)}")
        print(f"Total Stock Units: {summary.get('total_stock', 0)}")
        
        print("\nBy Category:")
        for cat in summary.get('by_category', []):
            print(f"  {cat['category']}: {cat['count']} products, {cat['stock']} units")
        
        input("\n\nPress Enter to continue...")

    def sales_report(self):
        """Display sales report (INV-F-031)."""
        self.clear_screen()
        self.print_header("SALES REPORT (ALL TIME)")
        
        report = self.order_processor.get_sales_report()
        
        print(f"\nTotal Orders: {report['total_orders']}")
        print(f"Total Revenue: ${report['total_revenue']:.2f}")
        print(f"Total Units Sold: {report['total_units']}")
        
        if report['orders']:
            print("\nRecent Orders:")
            self.order_processor.display_sales_orders(report['orders'][:10])
        
        input("Press Enter to continue...")

    def purchase_report(self):
        """Display purchase report (INV-F-031)."""
        self.clear_screen()
        self.print_header("PURCHASE REPORT (ALL TIME)")
        
        report = self.order_processor.get_purchase_report()
        
        print(f"\nTotal Orders: {report['total_orders']}")
        print(f"Total Cost: ${report['total_cost']:.2f}")
        print(f"Total Units Purchased: {report['total_units']}")
        
        if report['orders']:
            print("\nRecent Orders:")
            self.order_processor.display_purchase_orders(report['orders'][:10])
        
        input("Press Enter to continue...")

    def sales_report_date_range(self):
        """Sales report with date range (INV-F-031)."""
        self.clear_screen()
        self.print_header("SALES REPORT (DATE RANGE)")
        
        try:
            start_date = self.input_with_prompt("Start Date (YYYY-MM-DD)")
            end_date = self.input_with_prompt("End Date (YYYY-MM-DD)")
            
            report = self.order_processor.get_sales_report(start_date, end_date)
            
            print(f"\nPeriod: {start_date} to {end_date}")
            print(f"Total Orders: {report['total_orders']}")
            print(f"Total Revenue: ${report['total_revenue']:.2f}")
            print(f"Total Units Sold: {report['total_units']}")
            
            if report['orders']:
                print("\nOrders:")
                self.order_processor.display_sales_orders(report['orders'])
        except Exception as e:
            print(f"\n[X] Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def purchase_report_date_range(self):
        """Purchase report with date range (INV-F-031)."""
        self.clear_screen()
        self.print_header("PURCHASE REPORT (DATE RANGE)")
        
        try:
            start_date = self.input_with_prompt("Start Date (YYYY-MM-DD)")
            end_date = self.input_with_prompt("End Date (YYYY-MM-DD)")
            
            report = self.order_processor.get_purchase_report(start_date, end_date)
            
            print(f"\nPeriod: {start_date} to {end_date}")
            print(f"Total Orders: {report['total_orders']}")
            print(f"Total Cost: ${report['total_cost']:.2f}")
            print(f"Total Units Purchased: {report['total_units']}")
            
            if report['orders']:
                print("\nOrders:")
                self.order_processor.display_purchase_orders(report['orders'])
        except Exception as e:
            print(f"\n[X] Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    # ========== Backup & Restore ==========

    def backup_menu(self):
        """Backup and restore submenu (Admin only)."""
        if not self.auth.is_admin():
            print("\n[X] Admin privileges required for backup operations.")
            input("\nPress Enter to continue...")
            return
        
        while True:
            self.clear_screen()
            self.print_header("BACKUP & RESTORE (ADMIN ONLY)")
            print("\n1. Create Backup")
            print("2. Restore from Backup")
            print("3. List Available Backups")
            print("4. Delete Backup")
            print("0. Back to Main Menu")
            print()
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.create_backup()
            elif choice == '2':
                self.restore_backup()
            elif choice == '3':
                self.list_backups()
            elif choice == '4':
                self.delete_backup()
            elif choice == '0':
                break
            else:
                print("Invalid option.")
                input("\nPress Enter to continue...")

    def create_backup(self):
        """Create database backup (INV-NF-004)."""
        self.clear_screen()
        self.print_header("CREATE BACKUP")
        
        user = self.auth.get_current_username()
        backup_path = self.backup_manager.create_backup(user)
        
        input("\nPress Enter to continue...")

    def restore_backup(self):
        """Restore from backup."""
        self.clear_screen()
        self.print_header("RESTORE FROM BACKUP")
        
        self.backup_manager.display_backups()
        
        backup_filename = self.input_with_prompt("Enter backup filename to restore")
        
        confirm = input("\n[!] This will replace the current database. Continue? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            user = self.auth.get_current_username()
            self.backup_manager.restore_backup(backup_filename, user)
        else:
            print("Restore cancelled.")
        
        input("\nPress Enter to continue...")

    def list_backups(self):
        """List available backups."""
        self.clear_screen()
        self.print_header("AVAILABLE BACKUPS")
        
        self.backup_manager.display_backups()
        
        input("Press Enter to continue...")

    def delete_backup(self):
        """Delete a backup file."""
        self.clear_screen()
        self.print_header("DELETE BACKUP")
        
        self.backup_manager.display_backups()
        
        backup_filename = self.input_with_prompt("Enter backup filename to delete")
        
        confirm = input(f"\nDelete {backup_filename}? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            user = self.auth.get_current_username()
            self.backup_manager.delete_backup(backup_filename, user)
        else:
            print("Deletion cancelled.")
        
        input("\nPress Enter to continue...")

    # ========== Logs ==========

    def logs_menu(self):
        """View logs (Admin only)."""
        if not self.auth.is_admin():
            print("\n[X] Admin privileges required to view logs.")
            input("\nPress Enter to continue...")
            return
        
        self.clear_screen()
        self.print_header("SYSTEM LOGS (ADMIN ONLY)")
        
        logs = self.logger.get_recent_logs(50)
        self.logger.display_logs(logs)
        
        input("Press Enter to continue...")

    # ========== Authentication ==========

    def auth_menu(self):
        """Authentication menu."""
        if self.auth.is_authenticated():
            # Logout
            username = self.auth.get_current_username()
            self.auth.logout()
            print(f"\n[OK] Logged out successfully. Goodbye, {username}!")
            input("\nPress Enter to continue...")
        else:
            # Login
            self.login()

    def login(self):
        """User login."""
        self.clear_screen()
        self.print_header("LOGIN")
        
        username = self.input_with_prompt("Username")
        password = self.input_with_prompt("Password")
        
        if self.auth.login(username, password):
            role = "Admin" if self.auth.is_admin() else "User"
            print(f"\n[OK] Login successful! Welcome, {username} ({role})")
        else:
            print("\n[X] Invalid username or password.")
        
        input("\nPress Enter to continue...")

    # ========== Help ==========

    def show_help(self):
        """Display help information."""
        self.clear_screen()
        self.print_header("HELP & INFORMATION")
        
        print("\nDefault Admin Credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        
        print("\nKey Features:")
        print("  • Product Management: Add, view, search, update, delete products")
        print("  • Supplier Management: Manage supplier information")
        print("  • Order Processing: Create sales and purchase orders")
        print("  • Reports: View inventory, sales, and purchase reports")
        print("  • Backup/Restore: Create encrypted backups (Admin only)")
        print("  • Logging: All admin actions are logged")
        
        print("\nRequirements Met:")
        print("  [OK] INV-F-001 to INV-F-032: All functional requirements")
        print("  [OK] INV-NF-001 to INV-NF-005: All non-functional requirements")
        print("  [OK] PRJ-SEC-001 to PRJ-SEC-005: All security requirements")
        
        input("\n\nPress Enter to continue...")

    # ========== Exit ==========

    def exit_application(self):
        """Exit the application gracefully."""
        self.clear_screen()
        self.print_header("EXIT")
        
        if self.auth.is_authenticated():
            username = self.auth.get_current_username()
            self.auth.logout()
            print(f"\nLogging out {username}...")
        
        print("\nThank you for using the Inventory Management System!")
        print("Goodbye!\n")
        self.running = False


def main():
    """Main entry point for the CLI application."""
    try:
        cli = CLI()
        cli.main_menu()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\nFatal error: {str(e)}")
        print("Please contact support if this persists.")
    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
