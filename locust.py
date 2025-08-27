from locust import HttpUser, task, between

class MyUser(HttpUser):
    wait_time = between(1, 5)
    host = "http://127.0.0.1:8000"   # base URL

    @task
    def load_home_page(self):
        self.client.get("/")
