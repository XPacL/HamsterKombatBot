from dataclasses import dataclass

from bot.core.web_client import WebClient
from bot.utils import logger
import threading
import asyncio


@dataclass
class Promo:
    client_id: str
    promo_app: str
    promo_id: str


class PromoKeyGenerator:
    def __init__(self, web_client: WebClient):
        self.web_client = web_client
        self.promos_queue = []
        self.available_promos = {}  # promo_id: list[str]
        self.lock = threading.Lock()
        self.queue_lock = threading.Lock()

    def consume_promo_code(self, promo_id: str) -> str | None:
        self.lock.acquire()
        try:
            if self.available_promos.__contains__(promo_id):
                promo_codes: list[str] = list(self.available_promos[promo_id])
                if len(promo_codes) != 0:
                    promo_code = promo_codes.pop(0)
                    if len(promo_codes) == 0:
                        self.available_promos.pop(promo_id)
                    return promo_code
            return None
        finally:
            self.lock.release()

    def add_promo_to_queue(self, promo: Promo):
        self.queue_lock.acquire()
        try:
            if promo in self.promos_queue:
                return
            self.promos_queue.append(promo)
        finally:
            self.queue_lock.release()

    def remove_promo_from_queue(self, promo: Promo) -> bool:
        self.queue_lock.acquire()
        try:
            if promo not in self.promos_queue:
                return False
            self.promos_queue.remove(promo)
            return True
        finally:
            self.queue_lock.release()

    async def run(self):
        while True:
            promo = self.__get_next_promo()
            promo_code = await self.__generate_promo_key(promo)
            self.__add_to_available_promos(promo, promo_code)
            await asyncio.sleep(delay=3 * 60)

    def __get_next_promo(self) -> Promo | None:
        self.queue_lock.acquire()
        try:
            if len(self.promos_queue) == 0:
                return None
            return self.promos_queue[0]
        finally:
            self.queue_lock.release()

    def __add_to_available_promos(self, promo: Promo, promo_code: str):
        self.lock.acquire()
        try:
            if self.available_promos.__contains__(promo.promo_id):
                self.available_promos[promo.promo_id].append(promo_code)
            else:
                self.available_promos[promo.promo_id] = [promo_code]
        finally:
            self.lock.release()

    async def __generate_promo_key(self, promo: Promo) -> str:
        logger.info("Start generating promo key")
        auth_token = await self.web_client.login_gamepromo(app_token=promo.promo_app)
        await asyncio.sleep(delay=5)
        has_code = False
        while not has_code:
            has_code = await self.web_client.register_event(
                token=auth_token,
                promo_id=promo.promo_id
            )
            logger.info("Registered event for promo code")
            await asyncio.sleep(delay=25)

        logger.info("Promo code is available")

        return await self.web_client.create_code(
            token=auth_token,
            promo_id=promo.promo_id
        )
