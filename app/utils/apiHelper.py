import httpx
import os
import asyncio

from app.utils.singleton import Singleton


class ApiHelper(metaclass=Singleton):
    def __init__(self):
        self.fhir_client = httpx.AsyncClient(
            base_url="https://hapi.35.229.200.151.nip.io/fhir",
            headers={
                "X-API-KEY": os.getenv("X-API-KEY"),
            },
            timeout=10.0,
        )
        self.apim_client = httpx.AsyncClient(
            base_url="https://api.example.com/getToken",
            timeout=10.0,
        )

    async def stop(self):
        """Gracefully shutdown. Call from FastAPI shutdown hook."""
        await asyncio.gather(
            self.fhir_client.aclose(),
            self.apim_client.aclose(),
        )
        self.fhir_client = None
        self.apim_client = None

    async def getFHIRAPIDocs(self):
        try:
            response = await self.fhir_client.get("/api-docs")
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            print(f"FHIR API error: {e}")
            return None

    async def getFHIR(self, url, params):
        try:
            response = await self.fhir_client.get(url=url, params=params)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            print(f"FHIR API error: {e}")
            return None

    async def getToken(self, data):
        try:
            response = await self.apim_client.post(url="/", data=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Token API error: {e}")
            return {"error": str(e)}

    async def verify_token(self, token: str) -> tuple[bool, dict]:
        if token.startswith("Bearer "):
            token = token[len("Bearer ") :]
        try:
            response = await self.apim_client.post(
                url="/",
                data={"strategy": "jwt", "accessToken": token},
            )
            response.raise_for_status()
            return True, response.json()
        except httpx.HTTPError as e:
            return False, {"error": f"Invalid token: {e}"}
