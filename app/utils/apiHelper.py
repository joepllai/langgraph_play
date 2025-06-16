import httpx

from app.utils.singleton import Singleton


class GetResponse:
    result: any
    status: str


class ApiHelper(metaclass=Singleton):
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.apim_url = "https://api.example.com/getToken"

    async def stop(self):
        """Gracefully shutdown. Call from FastAPI shutdown hook."""
        await self.client.aclose()
        self.client = None

    async def getToken(self, data) -> GetResponse:
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
