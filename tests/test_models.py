# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""

import os
import logging
import unittest
from decimal import Decimal
from unittest.mock import MagicMock
from flask import Flask, Response
from service.models import Product, Category, db
from service.common import error_handlers, status, log_handlers
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.remove()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50,
                          available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Fetch it back
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Change it an save it
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # delete the product and make sure it isn't in the database
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(products, [])
        # Create 5 Products
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # See if we get back 5 products
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_serialize_product(self):
        """Test serialization of a Product"""
        product = Product(name="Test Product", description="Test Description",
                          price=10.0, available=True, category=Category.CLOTHS)
        serialized_product = product.serialize()
        self.assertIsInstance(serialized_product, dict)
        self.assertEqual(serialized_product['name'], "Test Product")
        self.assertEqual(serialized_product['description'], "Test Description")
        self.assertEqual(serialized_product['price'], '10.0')
        self.assertEqual(serialized_product['available'], True)
        self.assertEqual(serialized_product['category'], "CLOTHS")

    def test_deserialize_product(self):
        """Test deserialization of a Product"""
        data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': '10.0',
            'available': True,
            'category': 'CLOTHS'
        }
        product = Product()
        product.deserialize(data)
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.description, "Test Description")
        self.assertEqual(product.price, 10.0)
        self.assertEqual(product.available, True)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_init_db(self):
        """Test initialization of the database"""
        with self.assertRaises(AttributeError):
            Product.init_db(None)

    def test_find_by_category(self):
        """Test finding products by category"""
        product1 = Product(name="Test Product 1", description="Test Description 1",
                           price=10.0, available=True, category=Category.CLOTHS)
        product2 = Product(name="Test Product 2", description="Test Description 2",
                           price=20.0, available=False, category=Category.FOOD)
        db.session.add(product1)
        db.session.add(product2)
        db.session.commit()
        found = Product.find_by_category(Category.CLOTHS)
        found_list = list(found)
        self.assertEqual(len(found_list), 1)
        self.assertEqual(found_list[0].name, "Test Product 1")

    def test_find_by_price(self):
        """It should Find Products by Price"""
        # Create products with different prices
        product1 = Product(name="Product1", description="Description1",
                           price=10.0, available=True, category=Category.CLOTHS)
        product2 = Product(name="Product2", description="Description2",
                           price=20.0, available=True, category=Category.FOOD)
        product3 = Product(name="Product3", description="Description3",
                           price=30.0, available=True, category=Category.HOUSEWARES)

        # Add products to the database
        db.session.add_all([product1, product2, product3])
        db.session.commit()

        # Test finding products by price
        found_products = Product.find_by_price(20.0).all()  # Execute the query and get results

        # Assert that the correct product is found
        self.assertEqual(len(found_products), 1)
        self.assertEqual(found_products[0].name, "Product2")


class TestErrorHandlers(unittest.TestCase):
    """Test Cases for Error Handlers"""

    def setUp(self):
        """Set up Flask app for testing"""
        self.app = Flask(__name__)

    def test_bad_request_handler(self):
        """Test the bad request handler"""
        with self.app.app_context():
            error = ValueError("Test error")
            response = error_handlers.bad_request(error)
            self.assertEqual(response[1], status.HTTP_400_BAD_REQUEST)
            self.assertIsInstance(response[0], Response)
            self.assertIn("Bad Request", response[0].get_json()["error"])
            self.assertIn("Test error", response[0].get_json()["message"])

    def test_not_found_handler(self):
        """Test the not found handler"""
        with self.app.app_context():
            error = ValueError("Test error")
            response = error_handlers.not_found(error)
            self.assertEqual(response[1], status.HTTP_404_NOT_FOUND)
            self.assertIsInstance(response[0], Response)
            self.assertIn("Not Found", response[0].get_json()["error"])
            self.assertIn("Test error", response[0].get_json()["message"])

    def test_method_not_supported_handler(self):
        """Test the method not supported handler"""
        with self.app.app_context():
            error = ValueError("Test error")
            response = error_handlers.method_not_supported(error)
            self.assertEqual(response[1], status.HTTP_405_METHOD_NOT_ALLOWED)
            self.assertIsInstance(response[0], Response)
            self.assertIn("Method not Allowed", response[0].get_json()["error"])
            self.assertIn("Test error", response[0].get_json()["message"])

    def test_request_validation_error_handler(self):
        """Test the request validation error handler"""
        with self.app.app_context():
            error = error_handlers.DataValidationError("Test error")
            response = error_handlers.request_validation_error(error)
            self.assertEqual(response[1], status.HTTP_400_BAD_REQUEST)
            self.assertIsInstance(response[0], Response)
            self.assertIn("Bad Request", response[0].get_json()["error"])
            self.assertIn("Test error", response[0].get_json()["message"])

    def test_internal_server_error_handler(self):
        """Test the internal server error handler"""
        with self.app.app_context():
            error = ValueError("Test error")
            response = error_handlers.internal_server_error(error)
            self.assertEqual(response[1], status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIsInstance(response[0], Response)
            self.assertIn("Internal Server Error", response[0].get_json()["error"])
            self.assertIn("Test error", response[0].get_json()["message"])


class TestLogHandlers(unittest.TestCase):
    """Test Cases for Log Handlers"""

    def test_init_logging(self):
        """Test initialization of logging"""
        # Create a mock Flask app
        test_app = MagicMock()
        logger_name = "test_logger"

        # Set the logger levels explicitly
        test_app.logger.level = logging.INFO
        gunicorn_logger = logging.getLogger(logger_name)
        gunicorn_logger.setLevel(logging.INFO)

        # Call the init_logging function
        log_handlers.init_logging(test_app, logger_name)

        # Verify that the logger propagation is turned off
        self.assertFalse(test_app.logger.propagate)

        # Verify that the logger's handlers and level are set as expected
        self.assertEqual(test_app.logger.handlers, gunicorn_logger.handlers)
        self.assertEqual(test_app.logger.level, gunicorn_logger.level)

        # Verify that the log format is consistent for all handlers
        format_string = "[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s"
        formatter = logging.Formatter(format_string, "%Y-%m-%d %H:%M:%S %z")
        for handler in test_app.logger.handlers:
            self.assertEqual(handler.formatter.get_fmt(), formatter.get_fmt())  # Check format string
            self.assertEqual(handler.formatter.get_style(), formatter.get_style())  # Check style

        # Verify that the info message is logged
        test_app.logger.info.assert_called_with("Logging handler established")


if __name__ == '__main__':
    unittest.main()
