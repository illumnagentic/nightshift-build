from fastapi import FastAPI
from workers import WorkerEntrypoint
import asgi

# Routes are added on a router with prefix "/api", the base URL the web app proxies to.
app = FastAPI()


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request.js_object, self.env)
