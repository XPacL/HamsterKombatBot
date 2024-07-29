from dataclasses import dataclass
from enum import Enum, StrEnum

from bot.config.config import settings


@dataclass
class ReceivedPromo:
    promo_id: str
    receive_keys_total: int
    receive_keys_today: int
    receive_keys_last_time: str

    def __init__(self, data: dict):
        self.promo_id = data.get("promoId")
        self.receive_keys_total = data.get("receiveKeysTotal")
        self.receive_keys_today = data.get("receiveKeysToday")
        self.receive_keys_last_time = data.get("receiveKeysLastTime")


# pylint: disable=R0902
@dataclass
class Profile:
    id: str
    balance: float
    earn_per_hour: float
    earn_per_sec: float
    available_energy: int
    energy_recover_per_sec: int
    earn_per_tap: float
    max_energy: int
    last_passive_earn: float
    exchange_id: str | None
    last_energy_boost_time: int
    balance_keys: int
    promos: list[ReceivedPromo]

    def __init__(self, data: dict):
        self.id = data.get('id')
        self.balance = data.get('balanceCoins', 0)
        self.earn_per_hour = data.get('earnPassivePerHour', 0)
        self.earn_per_sec = data.get('earnPassivePerSec', 0)
        self.available_energy = data.get('availableTaps', 0)
        self.energy_recover_per_sec = data.get('tapsRecoverPerSec', 0)
        self.earn_per_tap = data.get('earnPerTap', 0)
        self.max_energy = data.get('maxTaps', 0)
        self.last_passive_earn = data.get('lastPassiveEarn', 0)
        self.exchange_id = data.get('exchangeId')
        self.balance_keys = data.get('balanceKeys', 0)
        self.promos = list(map(lambda p: ReceivedPromo(data=p), data.get('promos'))) if data.__contains__(
            'promos') else []
        try:
            self.last_energy_boost_time = next(
                (boost for boost in data["boosts"] if boost['id'] == 'BoostFullAvailableTaps'), {}
            ).get("lastUpgradeAt", 0)
        except:
            self.last_energy_boost_time = 0

    def get_available_taps(self):
        return int(float(self.available_energy) / self.earn_per_tap)

    def get_spending_balance(self):
        return self.balance - settings.MIN_BALANCE


@dataclass
class PromoState:
    id: str
    receive_keys_today: int
    receive_keys_refresh_sec: int
    available_keys_per_day: int

    def __init__(self, data: dict, promo_state: dict | None):
        self.id = data.get('promoId')
        if promo_state is not None:
            self.receive_keys_today = promo_state.get("receiveKeysToday")
            self.receive_keys_refresh_sec = promo_state.get("receiveKeysRefreshSec")
        else:
            self.receive_keys_today = 0
            self.receive_keys_refresh_sec = 0
        self.available_keys_per_day = data.get('keysPerDay')


@dataclass
class Upgrade:
    id: str
    name: str
    level: int
    price: float
    earn_per_hour: float
    is_available: bool
    is_expired: bool
    cooldown_seconds: int
    max_level: int
    welcome_coins: int
    condition: str

    def __init__(self, data: dict):
        self.id = data["id"]
        self.name = data["name"]
        self.level = data["level"]
        self.price = data["price"]
        self.earn_per_hour = data["profitPerHourDelta"]
        self.is_available = data["isAvailable"]
        self.is_expired = data["isExpired"]
        self.cooldown_seconds = data.get("cooldownSeconds", 0)
        self.max_level = data.get("maxLevel", data["level"])
        self.welcome_coins = data.get("welcomeCoins", 0)
        self.condition = data.get("condition")

    def calculate_significance(self, profile: Profile) -> float:
        if self.earn_per_hour == 0:
            return float('inf')
        if profile.earn_per_hour == 0:
            return self.price / self.earn_per_hour
        return self.price / self.earn_per_hour \
            + self.cooldown_seconds / 3600 \
            + max((self.price - profile.get_spending_balance()) / profile.earn_per_hour, 0)

    def can_upgrade(self) -> bool:
        return self.is_available \
            and not self.is_expired \
            and self.max_level >= self.level


@dataclass
class Boost:
    id: str
    cooldown_seconds: int
    level: int
    max_level: int

    def __init__(self, data: dict):
        self.id = data["id"]
        self.cooldown_seconds = data.get("cooldownSeconds", 0)
        self.level = data.get("level", 0)
        self.max_level = data.get("maxLevel", self.level)


@dataclass
class Task:
    id: str
    is_completed: bool
    reward_coins: int
    days: int

    def __init__(self, data: dict):
        self.id = data["id"]
        self.is_completed = data["isCompleted"]
        self.reward_coins = data.get("rewardCoins", 0)
        self.days = data.get("days", 0)


@dataclass
class DailyCombo:
    bonus_coins: int
    is_claimed: bool
    remain_seconds: int
    upgrade_ids: list[str]

    def __init__(self, data: dict):
        self.bonus_coins = data["bonusCoins"]
        self.is_claimed = data["isClaimed"]
        self.remain_seconds = data["remainSeconds"]
        self.upgrade_ids = data["upgradeIds"]


@dataclass
class DailyCipher:
    cipher: str
    bonus_coins: int
    is_claimed: bool

    def __init__(self, data: dict):
        self.cipher = data["cipher"]
        self.bonus_coins = data["bonusCoins"]
        self.is_claimed = data["isClaimed"]


@dataclass
class DailyKeysMiniGame:
    start_date: str
    level_config: str
    youtube_url: str
    bonus_keys: int
    is_claimed: bool
    total_seconds_to_next_attempt: int
    remain_seconds_to_guess: float
    remain_seconds: float
    remain_seconds_to_next_attempt: float

    def __init__(self, data: dict):
        self.start_date = data["startDate"]
        self.level_config = data["levelConfig"]
        self.youtube_url = data["youtubeUrl"]
        self.bonus_keys = data["bonusKeys"]
        self.is_claimed = data["isClaimed"]
        self.total_seconds_to_next_attempt = data["totalSecondsToNextAttempt"]
        self.remain_seconds_to_guess = data["remainSecondsToGuess"]
        self.remain_seconds = data["remainSeconds"]
        self.remain_seconds_to_next_attempt = data["remainSecondsToNextAttempt"]


@dataclass
class Promo:
    promo_app_id: str
    promo_id: str
    prefix: str
    events_count: int
    codes_per_day: int
    keys_per_day: int
    keys_per_code: int
    blocked: bool

    def __init__(self, data: dict, promo_app_id: str, blocked: bool):
        self.promo_app_id = promo_app_id
        self.promo_id = data["promoId"]
        self.prefix = data["prefix"]
        self.events_count = data["eventsCount"]
        self.codes_per_day = data["codesPerDay"]
        self.keys_per_day = data["keysPerDay"]
        self.keys_per_code = data["keysPerCode"]
        self.blocked = data["blocked"] or blocked


@dataclass
class Config:
    daily_cipher: DailyCipher
    daily_keys_mini_game: DailyKeysMiniGame
    promos: list[Promo]

    def __init__(self, data: dict):
        self.daily_cipher = DailyCipher(data=data["dailyCipher"])
        self.daily_keys_mini_game = DailyKeysMiniGame(data=data["dailyKeysMiniGame"])
        self.promos = [Promo(data=promo, promo_app_id=promos["token"], blocked=promos["blocked"]) for promos in data.get("clickerConfig").get("promos").get("apps") for promo in promos["promos"]]


class SleepReason(Enum):
    WAIT_UPGRADE_COOLDOWN = 1
    WAIT_UPGRADE_MONEY = 2
    WAIT_ENERGY_RECOVER = 3
    WAIT_PASSIVE_EARN = 4
    WAIT_DAILY_KEYS_MINI_GAME = 5
    WAIT_PROMO_CODES = 6


@dataclass
class Sleep:
    delay: float
    sleep_reason: SleepReason
    created_time: float


@dataclass
class AirDropTask:
    id: str
    is_completed: bool

    def __init__(self, data: dict):
        self.id = data["id"]
        self.is_completed = data["isCompleted"]


class AirDropTaskId(StrEnum):
    CONNECT_TON_WALLET = "airdrop_connect_ton_wallet"
