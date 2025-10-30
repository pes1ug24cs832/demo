"""
Product Manager Module
Manages product inventory operations (CRUD).
Implements INV-F-001, INV-F-002, INV-F-003, INV-F-032.
"""

from typing import List, Dict, Optional
from .storage import StorageManager
from .logger import LogManager
from .config import LOW_STOCK_THRESHOLD


class ProductManager:
    """Manages product inventory."""

    def __init__(self, storage: StorageManager = None, logger: LogManager = None):
        """
        Initialize product manager.

        Args:
            storage: StorageManager instance (optional)
            logger: LogManager instance (optional)
        """
        self.storage = storage or StorageManager()
        self.logger = logger or LogManager(self.storage)

    def add_product(self, sku: str, name: str, price: float, category: str,
                   stock: int, description: str = "", user: str = "system") -> Optional[int]:
        """
        Add new product to inventory (INV-F-001).

        Args:
            sku: Unique product SKU
            name: Product name
            price: Product price
            category: Product category
            stock: Initial stock quantity
            description: Product description
            user: Username performing the action

        Returns:
            Product ID if successful, None if SKU already exists
        """
        # Check if SKU already exists
        existing = self.storage.get_product_by_sku(sku)
        if existing:
            return None

        # Validate inputs
        if price < 0:
            raise ValueError("Price cannot be negative")
        if stock < 0:
            raise ValueError("Stock cannot be negative")

        # Add product
        product_id = self.storage.add_product(sku, name, price, category, stock, description)

        # Log action
        self.logger.log_action(
            user,
            "ADD_PRODUCT",
            f"Added product: {name} (SKU: {sku})"
        )

        return product_id

    def get_all_products(self) -> List[Dict]:
        """
        Get all products (INV-F-002).

        Returns:
            List of product dictionaries
        """
        return self.storage.get_all_products()

    def get_product(self, product_id: int) -> Optional[Dict]:
        """
        Get product by ID.

        Args:
            product_id: Product ID

        Returns:
            Product dictionary or None if not found
        """
        return self.storage.get_product_by_id(product_id)

    def search_products(self, search_term: str) -> List[Dict]:
        """
        Search products by name, SKU, or category (INV-F-002).

        Args:
            search_term: Search string

        Returns:
            List of matching product dictionaries
        """
        return self.storage.search_products(search_term)

    def update_product(self, product_id: int, user: str = "system", **kwargs) -> bool:
        """
        Update product details (INV-F-003).

        Args:
            product_id: Product ID to update
            user: Username performing the action
            **kwargs: Fields to update (name, price, category, stock, description)

        Returns:
            True if successful, False otherwise
        """
        # Validate price and stock if being updated
        if 'price' in kwargs and kwargs['price'] < 0:
            raise ValueError("Price cannot be negative")
        if 'stock' in kwargs and kwargs['stock'] < 0:
            raise ValueError("Stock cannot be negative")

        # Get current product for logging
        product = self.get_product(product_id)
        if not product:
            return False

        # Update product
        success = self.storage.update_product(product_id, **kwargs)

        if success:
            # Log action
            updates = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            self.logger.log_action(
                user,
                "UPDATE_PRODUCT",
                f"Updated product {product['name']} (ID: {product_id}): {updates}"
            )

        return success

    def delete_product(self, product_id: int, user: str = "system") -> bool:
        """
        Delete product (admin only).

        Args:
            product_id: Product ID to delete
            user: Username performing the action

        Returns:
            True if successful, False otherwise
        """
        # Get product for logging before deletion
        product = self.get_product(product_id)
        if not product:
            return False

        # Delete product
        success = self.storage.delete_product(product_id)

        if success:
            # Log action (PRJ-SEC-003)
            self.logger.log_action(
                user,
                "DELETE_PRODUCT",
                f"Deleted product: {product['name']} (SKU: {product['sku']}, ID: {product_id})"
            )

        return success

    def get_low_stock_products(self, threshold: int = None) -> List[Dict]:
        """
        Get products with low stock (INV-F-032).

        Args:
            threshold: Stock threshold (uses config default if not provided)

        Returns:
            List of products with stock at or below threshold
        """
        threshold = threshold if threshold is not None else LOW_STOCK_THRESHOLD
        return self.storage.get_low_stock_products(threshold)

    def check_stock_availability(self, product_id: int, quantity: int) -> bool:
        """
        Check if sufficient stock is available.

        Args:
            product_id: Product ID
            quantity: Required quantity

        Returns:
            True if sufficient stock available, False otherwise
        """
        product = self.get_product(product_id)
        if not product:
            return False
        return product['stock'] >= quantity

    def adjust_stock(self, product_id: int, quantity_change: int,
                    user: str = "system") -> bool:
        """
        Adjust product stock by a delta amount.

        Args:
            product_id: Product ID
            quantity_change: Amount to add (positive) or remove (negative)
            user: Username performing the action

        Returns:
            True if successful, False otherwise
        """
        product = self.get_product(product_id)
        if not product:
            return False

        new_stock = product['stock'] + quantity_change

        if new_stock < 0:
            raise ValueError("Insufficient stock for this operation")

        return self.update_product(product_id, stock=new_stock, user=user)

    def display_products(self, products: List[Dict]):
        """
        Display products in a formatted table.

        Args:
            products: List of product dictionaries to display
        """
        if not products:
            print("\nNo products found.")
            return

        print("\n" + "="*120)
        print(f"{'ID':<5} {'SKU':<12} {'Name':<25} {'Category':<15} {'Price':<10} {'Stock':<8} {'Description':<30}")
        print("="*120)

        for product in products:
            product_id = str(product.get('id', ''))[:4]
            sku = product.get('sku', '')[:11]
            name = product.get('name', '')[:24]
            category = product.get('category', '')[:14]
            price = f"${product.get('price', 0):.2f}"
            stock = str(product.get('stock', 0))
            description = product.get('description', '')[:29]

            print(f"{product_id:<5} {sku:<12} {name:<25} {category:<15} {price:<10} {stock:<8} {description:<30}")

        print("="*120 + "\n")
