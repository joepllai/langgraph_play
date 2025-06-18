import httpx
import os

from app.utils.singleton import Singleton

class ApiHelper(metaclass=Singleton):
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.apim_url = "https://api.example.com/getToken"
        self.fhir_url = "https://hapi.35.229.200.151.nip.io"

    async def stop(self):
        """Gracefully shutdown. Call from FastAPI shutdown hook."""
        await self.client.aclose()
        self.client = None

    async def getFHIRAPIDocs(self):
        response = await self.client.get(
            f"{self.fhir_url}/fhir/api-docs",
            headers={
                "X-API-KEY": os.getenv("X-API-KEY"),
            },
        )
        return response.text

    async def getToken(self, data):
        response = await self.client.post(
            self.apim_url,
            data=data,
        )
        return response.json()

    async def verify_token(self, token: str) -> tuple[bool, dict]:
        if token.startswith("Bearer "):
            token = token[len("Bearer ") :]
        response = await self.client.post(
            self.apim_url,
            data={"strategy": "jwt", "accessToken": token},
        )
        if response.status_code >= 200 and response.status_code < 400:
            return True, response.json()
        return False, {"error": "Invalid token"}
