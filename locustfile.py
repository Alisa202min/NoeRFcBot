import time
import random
from locust import HttpUser, task, between
from typing import List, Dict, Any
import json
import requests


class TelegramBotUser(HttpUser):
    """
    Locust user class for stress testing the Telegram bot's category hierarchy
    Simulates multiple users interacting with the bot API through webhook
    """
    
    # Wait between 1 and 3 seconds between tasks
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize user data when a new user starts"""
        # Generate a random user ID for this simulated user
        self.user_id = random.randint(100000, 999999)
        self.username = f"test_user_{self.user_id}"
        
        # Get or cache category data
        self.categories = self.get_categories()
    
    def get_categories(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get or generate category data for testing
        In a real environment, this would come from the database
        """
        # For testing, we'll use a hardcoded category structure
        return {
            "product": [
                {
                    "id": 1,
                    "name": "محصولات فرکانس پایین",
                    "parent_id": None,
                    "subcategories": [
                        {
                            "id": 3,
                            "name": "آنتن‌ها",
                            "parent_id": 1,
                            "subcategories": [
                                {
                                    "id": 6,
                                    "name": "آنتن‌های یکطرفه",
                                    "parent_id": 3,
                                    "subcategories": [
                                        {
                                            "id": 8,
                                            "name": "آنتن‌های یکطرفه موج کوتاه",
                                            "parent_id": 6,
                                            "subcategories": []
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
            "service": [
                {
                    "id": 9,
                    "name": "خدمات نصب",
                    "parent_id": None,
                    "subcategories": [
                        {
                            "id": 11,
                            "name": "نصب آنتن",
                            "parent_id": 9,
                            "subcategories": []
                        }
                    ]
                }
            ]
        }
    
    def create_update(self, text=None, callback_data=None) -> Dict[str, Any]:
        """
        Create a simulated Telegram update object
        
        Args:
            text: Message text (for commands)
            callback_data: Callback data (for inline button clicks)
            
        Returns:
            Dict representing a Telegram update
        """
        update = {
            "update_id": random.randint(10000000, 99999999)
        }
        
        if text:
            # Create a message update
            update["message"] = {
                "message_id": random.randint(1000, 9999),
                "from": {
                    "id": self.user_id,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": self.username,
                    "language_code": "fa"
                },
                "chat": {
                    "id": self.user_id,
                    "first_name": "Test",
                    "username": self.username,
                    "type": "private"
                },
                "date": int(time.time()),
                "text": text
            }
        elif callback_data:
            # Create a callback query update
            update["callback_query"] = {
                "id": f"{random.randint(100000000000, 999999999999)}",
                "from": {
                    "id": self.user_id,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": self.username,
                    "language_code": "fa"
                },
                "message": {
                    "message_id": random.randint(1000, 9999),
                    "from": {
                        "id": 7630601243,  # Bot ID
                        "is_bot": True,
                        "first_name": "RFCatalogbot",
                        "username": "RFCatalogbot"
                    },
                    "chat": {
                        "id": self.user_id,
                        "first_name": "Test",
                        "username": self.username,
                        "type": "private"
                    },
                    "date": int(time.time()) - 10,
                    "text": "متن پیام قبلی"
                },
                "chat_instance": f"-{random.randint(1000000000000000000, 9999999999999999999)}",
                "data": callback_data
            }
        
        return update
    
    @task(1)
    def start_command(self):
        """Simulate a user sending the /start command"""
        update = self.create_update(text="/start")
        response = self.client.post("/webhook", json=update)
        
        # Log success or failure
        if response.status_code == 200:
            self.environment.events.request_success.fire(
                request_type="POST",
                name="Start Command",
                response_time=response.elapsed.total_seconds() * 1000,
                response_length=len(response.text)
            )
        else:
            self.environment.events.request_failure.fire(
                request_type="POST",
                name="Start Command",
                response_time=response.elapsed.total_seconds() * 1000,
                exception=Exception(f"Status Code: {response.status_code}, Response: {response.text}")
            )
    
    @task(2)
    def products_command(self):
        """Simulate a user sending the /products command"""
        update = self.create_update(text="/products")
        response = self.client.post("/webhook", json=update)
        
        # Log success or failure
        if response.status_code == 200:
            self.environment.events.request_success.fire(
                request_type="POST",
                name="Products Command",
                response_time=response.elapsed.total_seconds() * 1000,
                response_length=len(response.text)
            )
        else:
            self.environment.events.request_failure.fire(
                request_type="POST",
                name="Products Command",
                response_time=response.elapsed.total_seconds() * 1000,
                exception=Exception(f"Status Code: {response.status_code}, Response: {response.text}")
            )
    
    @task(2)
    def services_command(self):
        """Simulate a user sending the /services command"""
        update = self.create_update(text="/services")
        response = self.client.post("/webhook", json=update)
        
        # Log success or failure
        if response.status_code == 200:
            self.environment.events.request_success.fire(
                request_type="POST",
                name="Services Command",
                response_time=response.elapsed.total_seconds() * 1000,
                response_length=len(response.text)
            )
        else:
            self.environment.events.request_failure.fire(
                request_type="POST",
                name="Services Command",
                response_time=response.elapsed.total_seconds() * 1000,
                exception=Exception(f"Status Code: {response.status_code}, Response: {response.text}")
            )
    
    @task(3)
    def select_category(self):
        """Simulate a user clicking on a category button"""
        # Randomly select a category type and ID
        cat_type = random.choice(["product", "service"])
        
        if cat_type == "product":
            category_id = random.choice([1, 3, 6, 8])
        else:
            category_id = random.choice([9, 11])
        
        # Create callback data in the format used by the bot
        callback_data = f"category:{category_id}:{cat_type}"
        update = self.create_update(callback_data=callback_data)
        response = self.client.post("/webhook", json=update)
        
        # Log success or failure
        if response.status_code == 200:
            self.environment.events.request_success.fire(
                request_type="POST",
                name=f"Select {cat_type.capitalize()} Category {category_id}",
                response_time=response.elapsed.total_seconds() * 1000,
                response_length=len(response.text)
            )
        else:
            self.environment.events.request_failure.fire(
                request_type="POST",
                name=f"Select {cat_type.capitalize()} Category {category_id}",
                response_time=response.elapsed.total_seconds() * 1000,
                exception=Exception(f"Status Code: {response.status_code}, Response: {response.text}")
            )
    
    @task(1)
    def navigate_back(self):
        """Simulate a user clicking the back button"""
        cat_type = random.choice(["product", "service"])
        callback_data = f"back:{cat_type}"
        update = self.create_update(callback_data=callback_data)
        response = self.client.post("/webhook", json=update)
        
        # Log success or failure
        if response.status_code == 200:
            self.environment.events.request_success.fire(
                request_type="POST",
                name=f"Navigate Back ({cat_type})",
                response_time=response.elapsed.total_seconds() * 1000,
                response_length=len(response.text)
            )
        else:
            self.environment.events.request_failure.fire(
                request_type="POST",
                name=f"Navigate Back ({cat_type})",
                response_time=response.elapsed.total_seconds() * 1000,
                exception=Exception(f"Status Code: {response.status_code}, Response: {response.text}")
            )
    
    @task(1)
    def browse_complete_hierarchy(self):
        """
        Simulate a user navigating through the complete category hierarchy
        This is a more complex task that chains multiple requests
        """
        # Start with /products command
        update = self.create_update(text="/products")
        response = self.client.post("/webhook", json=update)
        if response.status_code != 200:
            self.environment.events.request_failure.fire(
                request_type="POST",
                name="Browse Hierarchy - Initial Products",
                response_time=response.elapsed.total_seconds() * 1000,
                exception=Exception(f"Status Code: {response.status_code}")
            )
            return
        
        # Small delay to simulate user reading/deciding
        time.sleep(random.uniform(0.5, 1.5))
        
        # Select level 1 category
        update = self.create_update(callback_data="category:1:product")
        response = self.client.post("/webhook", json=update)
        if response.status_code != 200:
            self.environment.events.request_failure.fire(
                request_type="POST",
                name="Browse Hierarchy - Level 1",
                response_time=response.elapsed.total_seconds() * 1000,
                exception=Exception(f"Status Code: {response.status_code}")
            )
            return
        
        time.sleep(random.uniform(0.5, 1.5))
        
        # Select level 2 category
        update = self.create_update(callback_data="category:3:product")
        response = self.client.post("/webhook", json=update)
        if response.status_code != 200:
            self.environment.events.request_failure.fire(
                request_type="POST",
                name="Browse Hierarchy - Level 2",
                response_time=response.elapsed.total_seconds() * 1000,
                exception=Exception(f"Status Code: {response.status_code}")
            )
            return
        
        time.sleep(random.uniform(0.5, 1.5))
        
        # Select level 3 category
        update = self.create_update(callback_data="category:6:product")
        response = self.client.post("/webhook", json=update)
        if response.status_code != 200:
            self.environment.events.request_failure.fire(
                request_type="POST",
                name="Browse Hierarchy - Level 3",
                response_time=response.elapsed.total_seconds() * 1000,
                exception=Exception(f"Status Code: {response.status_code}")
            )
            return
        
        time.sleep(random.uniform(0.5, 1.5))
        
        # Select level 4 category (leaf node)
        update = self.create_update(callback_data="category:8:product")
        response = self.client.post("/webhook", json=update)
        if response.status_code != 200:
            self.environment.events.request_failure.fire(
                request_type="POST",
                name="Browse Hierarchy - Level 4",
                response_time=response.elapsed.total_seconds() * 1000,
                exception=Exception(f"Status Code: {response.status_code}")
            )
            return
        
        # Log success for the complete flow
        self.environment.events.request_success.fire(
            request_type="FLOW",
            name="Complete Hierarchy Navigation",
            response_time=0,  # Not applicable for flow
            response_length=0  # Not applicable for flow
        )