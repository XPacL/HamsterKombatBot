import json as json_parser
import uuid
from random import randint
from time import time

import aiohttp

from bot.core.headers import create_headers


class PromoKeysWebClient:

    @staticmethod
    def __generate_client_id():
        timestamp = int(time() * 1000)
        random_numbers = ''.join([str(randint(0, 9)) for _ in range(19)])
        client_id = f"{timestamp}-{random_numbers}"
        return client_id

    @staticmethod
    async def make_gamepromo_request(url: str, json: dict | None = None, auth_token: str | None = None) -> dict:
        default_headers = create_headers(
            json=json,
            host="api.gamepromo.io",
            origin="https://api.gamepromo.io"
        )
        async with aiohttp.ClientSession(headers=default_headers) as session:
            response = await session.post(url=url,
                                          headers={"Authorization": f"Bearer {auth_token}"} if auth_token else None,
                                          json=json)
            response_text = await response.text()
            if response.status != 422:
                response.raise_for_status()

        return json_parser.loads(response_text)

    async def login_gamepromo(self, app_token: str) -> str:
        response = await self.make_gamepromo_request(
            url='https://api.gamepromo.io/promo/login-client',
            json={
                "appToken": app_token,
                "clientId": self.__generate_client_id(),
                "clientOrigin": "deviceid"
            }
        )
        return response["clientToken"]

    async def register_event(self, token: str, promo_id: str) -> bool:
        response = await self.make_gamepromo_request(
            url='https://api.gamepromo.io/promo/register-event',
            json={
                "promoId": promo_id,
                "eventId": str(uuid.uuid4()),
                "eventOrigin": "undefined"
            },
            auth_token=token
        )

        return response["hasCode"]

    async def create_code(self, token: str, promo_id: str) -> str:
        response = await self.make_gamepromo_request(
            url='https://api.gamepromo.io/promo/create-code',
            json={"promoId": promo_id},
            auth_token=token
        )

        return response["promoCode"]