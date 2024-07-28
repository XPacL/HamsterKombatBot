import json as json_parser
import uuid
from enum import StrEnum
from random import randint
from time import time
import datetime

import aiohttp
from better_proxy import Proxy

from bot.config import API_URL
from bot.core.entities import AirDropTask, Boost, Upgrade, Profile, Task, DailyCombo, Config, AirDropTaskId, PromoState
from bot.core.headers import create_hamster_headers, create_headers
from bot.utils import logger
from bot.utils.client import Client


class Requests(StrEnum):
    CONFIG = f"{API_URL}/clicker/config"
    ME_TELEGRAM = f"{API_URL}/auth/me-telegram"
    TAP = f"{API_URL}/clicker/tap"
    BOOSTS_FOR_BUY = f"{API_URL}/clicker/boosts-for-buy"
    BUY_UPGRADE = f"{API_URL}/clicker/buy-upgrade"
    UPGRADES_FOR_BUY = f"{API_URL}/clicker/upgrades-for-buy"
    BUY_BOOST = f"{API_URL}/clicker/buy-boost"
    CHECK_TASK = f"{API_URL}/clicker/check-task"
    SELECT_EXCHANGE = f"{API_URL}/clicker/select-exchange"
    LIST_TASKS = f"{API_URL}/clicker/list-tasks"
    SYNC = f"{API_URL}/clicker/sync"
    CLAIM_DAILY_CIPHER = f"{API_URL}/clicker/claim-daily-cipher"
    CLAIM_DAILY_COMBO = f"{API_URL}/clicker/claim-daily-combo"
    REFERRAL_STAT = f"{API_URL}/clicker/referral-stat"
    LIST_AIRDROP_TASKS = f"{API_URL}/clicker/list-airdrop-tasks"
    CHECK_AIRDROP_TASK = f"{API_URL}/clicker/check-airdrop-task"
    START_KEYS_MINIGAME = f"{API_URL}/clicker/start-keys-minigame"
    CLAIM_DAILY_KEYS_MINIGAME = f"{API_URL}/clicker/claim-daily-keys-minigame"
    APPLY_PROMO = f"{API_URL}/clicker/apply-promo"
    GET_PROMOS = f"{API_URL}/clicker/get-promos"


class WebClient:
    def __init__(self, http_client: aiohttp.ClientSession, client: Client, proxy: str | None):
        self.http_client = http_client
        self.session_name = client.name
        self.http_client.headers["Authorization"] = f"Bearer {client.token}"
        self.proxy = proxy

    async def check_proxy(self, proxy: Proxy) -> None:
        try:
            response = await self.http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except aiohttp.ClientConnectorError as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def get_profile_data(self) -> Profile:
        response = await self.make_request(Requests.SYNC)
        profile_data = response.get('clickerUser') or response.get('found', {}).get('clickerUser', {})
        return Profile(data=profile_data)

    async def get_tasks(self) -> list[Task]:
        response = await self.make_request(Requests.LIST_TASKS)
        return list(map(lambda d: Task(data=d), response['tasks']))

    async def select_exchange(self, exchange_id: str) -> bool:
        await self.make_request(Requests.SELECT_EXCHANGE, json={'exchangeId': exchange_id})
        return True

    async def check_task(self, task_id: str) -> bool:
        response = await self.make_request(Requests.CHECK_TASK, json={'taskId': task_id})
        return response.get('task', {}).get('isCompleted', False)

    async def apply_boost(self, boost_id: str) -> Profile:
        response = await self.make_request(Requests.BUY_BOOST, json={'timestamp': time(), 'boostId': boost_id})
        profile_data = response.get('clickerUser') or response.get('found', {}).get('clickerUser', {})

        return Profile(data=profile_data)

    async def get_upgrades(self) -> tuple[list[Upgrade], DailyCombo]:
        response = await self.make_request(Requests.UPGRADES_FOR_BUY)
        return list(map(lambda x: Upgrade(data=x), response['upgradesForBuy'])), \
            DailyCombo(data=response.get('dailyCombo', {}))

    async def buy_upgrade(self, upgrade_id: str) -> tuple[Profile, list[Upgrade], DailyCombo]:
        response = await self.make_request(Requests.BUY_UPGRADE, json={'timestamp': time(), 'upgradeId': upgrade_id})
        if 'found' in response:
            response = response['found']
        profile_data = response.get('clickerUser')
        return Profile(data=profile_data), \
            list(map(lambda x: Upgrade(data=x), response.get('upgradesForBuy', []))), \
            DailyCombo(data=response.get('dailyCombo', {}))

    async def get_boosts(self) -> list[Boost]:
        response = await self.make_request(Requests.BOOSTS_FOR_BUY)
        return list(map(lambda x: Boost(data=x), response['boostsForBuy']))

    async def send_taps(self, available_energy: int, taps: int) -> Profile:
        response = await self.make_request(Requests.TAP,
                                           json={'availableTaps': available_energy, 'count': taps, 'timestamp': time()})
        profile_data = response.get('clickerUser') or response.get('found', {}).get('clickerUser', {})

        return Profile(data=profile_data)

    async def get_me_telegram(self) -> None:
        await self.make_request(Requests.ME_TELEGRAM)

    async def get_config(self) -> Config:
        response = await self.make_request(Requests.CONFIG)
        return Config(data=response)

    async def claim_daily_cipher(self, cipher: str) -> Profile:
        response = await self.make_request(Requests.CLAIM_DAILY_CIPHER, json={'cipher': cipher})
        if 'found' in response:
            response = response['found']
        return Profile(data=response.get('clickerUser'))

    async def claim_daily_combo(self) -> Profile:
        response = await self.make_request(Requests.CLAIM_DAILY_COMBO)
        if 'found' in response:
            response = response['found']
        return Profile(data=response.get('clickerUser'))

    async def get_referrals_count(self) -> int:
        response = await self.make_request(Requests.REFERRAL_STAT, json={'offset': 0})
        if 'found' in response:
            response = response['found']
        return response.get('count', 0)

    async def attach_wallet(self, wallet: str) -> bool:
        response = await self.make_request(Requests.CHECK_AIRDROP_TASK,
                                           json={'id': AirDropTaskId.CONNECT_TON_WALLET, 'walletAddress': wallet})
        return response.get('airdropTask', {}).get('isCompleted', False)

    async def start_keys_minigame(self):
        await self.make_request(Requests.START_KEYS_MINIGAME)

    async def claim_daily_keys_minigame(self, cipher: str) -> Profile:
        response = await self.make_request(Requests.CLAIM_DAILY_KEYS_MINIGAME, json={'cipher': cipher})
        if 'found' in response:
            response = response['found']
        return Profile(data=response.get('clickerUser'))

    async def get_airdrop_tasks(self) -> list[AirDropTask]:
        response = await self.make_request(Requests.LIST_AIRDROP_TASKS)
        return list(map(lambda d: AirDropTask(data=d), response['airdropTasks']))

    # noinspection PyMethodMayBeStatic
    async def fetch_daily_combo(self) -> dict:
        async with aiohttp.ClientSession() as http_client:  # we don't need the headers from self.http_client
            response = await http_client.get(url="https://anisovaleksey.github.io/HamsterKombatBot/daily_combo.json")
            return await response.json()

    async def apply_promo(self, promo_code: str) -> Profile:
        response = await self.make_request(Requests.APPLY_PROMO, json={"promoCode": promo_code})
        if 'found' in response:
            response = response['found']
        return Profile(data=response.get('clickerUser'))

    async def get_promos(self) -> list[PromoState]:
        response = await self.make_request(Requests.GET_PROMOS)
        promo_limits = {}
        for promo in response["promos"]:
            promo_limits[promo["promoId"]] = promo["keysPerDay"]
        return list(map(lambda x: PromoState(data=x, available_keys_per_day=promo_limits[x.promo["promoId"]]), response["states"]))

    async def make_request(self, request: Requests, json: dict | None = None) -> dict:
        response = await self.http_client.post(url=request,
                                               headers=create_hamster_headers(json),
                                               json=json)
        response_text = await response.text()
        if response.status != 422:
            response.raise_for_status()

        return json_parser.loads(response_text)

    # MINI-GAMES CODE GENERATION API
    @staticmethod
    def __generate_client_id():
        timestamp = int(time() * 1000)
        random_numbers = ''.join([str(randint(0, 9)) for _ in range(19)])
        client_id = f"{timestamp}-{random_numbers}"
        return client_id

    async def make_gamepromo_request(self, url: str, json: dict | None = None, auth_token: str | None = None) -> dict:
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