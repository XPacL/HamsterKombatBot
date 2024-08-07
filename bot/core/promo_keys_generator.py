from dataclasses import dataclass

from bot.core.promo_keys_web_client import PromoKeysWebClient
from bot.utils import logger
from bot.config import settings
from random import randint
import threading
import asyncio


@dataclass
class Promo:
    client_id: str
    promo_app: str
    promo_id: str
    min_wait_after_login: int


class PromoKeysGenerator:
    def __init__(self, web_client: PromoKeysWebClient):
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
                    else:
                        self.available_promos[promo_id] = promo_codes
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
            try:
                promo = self.__get_next_promo()
                if promo:
                    promo_code = await self.__generate_promo_key(promo)
                    self.__add_to_available_promos(promo, promo_code)
            except Exception as e:
                logger.error(f"Exception while generating promo key: {e}")

            sleep_time = randint(settings.SLEEP_INTERVAL_BETWEEN_PROMOCODES_GENERATIONS[0], settings.SLEEP_INTERVAL_BETWEEN_PROMOCODES_GENERATIONS[1])
            await asyncio.sleep(delay=float(sleep_time))

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

            logger.info(f"[Promo Keys Generator] Total available promo-codes: {len(self.available_promos[promo.promo_id])}")
        finally:
            self.lock.release()

    async def __generate_promo_key(self, promo: Promo) -> str:
        logger.info("[Promo Keys Generator] Start generating promo-code")
        auth_token = await self.web_client.login_gamepromo(app_token=promo.promo_app)
        wait_time = randint(promo.min_wait_after_login, promo.min_wait_after_login + 20)
        logger.info(f"[Promo Keys Generator] Successfully logged in | Waiting {wait_time} seconds before events registering")
        await asyncio.sleep(delay=wait_time)
        has_code = False
        while not has_code:
            try:
                has_code = await self.web_client.register_event(
                    token=auth_token,
                    promo_id=promo.promo_id
                )
                logger.info("[Promo Keys Generator] Registered event for promo-code")
            except Exception as e:
                logger.error(f"[Promo Keys Generator] Exception while generating promo-code: {e}")
            if not has_code:
                sleep_time = randint(settings.SLEEP_INTERVAL_BETWEEN_EVENTS_FOR_PROMOCODES[0], settings.SLEEP_INTERVAL_BETWEEN_EVENTS_FOR_PROMOCODES[1])
                await asyncio.sleep(delay=float(sleep_time))

        logger.info(f"[Promo Keys Generator] New promo-code is available")

        return await self.web_client.create_code(
            token=auth_token,
            promo_id=promo.promo_id
        )
