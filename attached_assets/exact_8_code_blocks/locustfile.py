from locust import HttpUser, task, between

class BotUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def send_products(self):
        self.client.post("/webhook", json={
            "update_id": 1,
            "message": {
                "message_id": 1,
                "chat": {"id": 123, "type": "private"},
                "from": {"id": 456, "is_bot": False},
                "text": "/products"
            }
        })