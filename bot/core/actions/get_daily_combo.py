import datetime
from time import time

from bot.core.entities import Upgrade
from bot.core.tapper import Tapper
from bot.utils import logger, format_number


async def get_daily_combo(bot: Tapper, most_profit_upgrade: Upgrade) -> Upgrade | None:
    reward_claimed = await bot.try_claim_daily_combo()
    if reward_claimed:
        return None

    combo, end_combo_timestamp = await fetch_daily_combo(bot)

    if len(combo) == 0:
        logger.info(f"{bot.session_name} | Daily combo not published")
        return None

    combo_upgrades: list[Upgrade] = list(
        filter(lambda u: u.id in combo and u.id not in bot.daily_combo.upgrade_ids, bot.upgrades)
    )

    if await check_daily_combo_is_possible(bot, combo_upgrades, end_combo_timestamp):
        combo_significance = await get_daily_combo_significance(bot, combo_upgrades)
        most_profit_upgrade_significance = most_profit_upgrade.calculate_significance(bot.profile)
        if combo_significance >= most_profit_upgrade_significance:
            logger.info(f"{bot.session_name} | Daily combo is not profitable "
                        f"| Combo payback: {combo_significance:.0f} hours "
                        f"| Most profit Upgrade: {most_profit_upgrade_significance:.0f} hours")
        else:
            return combo_upgrades[0]

    return None


async def get_daily_combo_significance(bot: Tapper, combo: list[Upgrade]) -> float:
    total_price = 0
    total_earn = 0
    welcome_coins = 0

    for upgrade in combo:
        total_price += upgrade.price
        total_earn += upgrade.earn_per_hour
        welcome_coins += upgrade.welcome_coins

    return (total_price - 5_000_000 - welcome_coins) / total_earn \
        + max((total_price - bot.profile.get_spending_balance()) / bot.profile.earn_per_hour, 0)


async def fetch_daily_combo(bot: Tapper) -> tuple[list[str], float]:
    response_json = await bot.web_client.fetch_daily_combo()
    combo = response_json.get('combo')
    start_combo_date = datetime.datetime \
        .strptime(response_json.get('date'), "%Y-%m-%d") \
        .replace(tzinfo=datetime.timezone.utc).replace(hour=12)
    end_combo_date = start_combo_date + datetime.timedelta(days=1)
    current_timestamp = time()

    if start_combo_date.timestamp() < current_timestamp < end_combo_date.timestamp():
        return combo, end_combo_date.timestamp()
    return [], end_combo_date.timestamp()


async def check_daily_combo_is_possible(bot: Tapper, combo: list[Upgrade], end_combo_timestamp: float) -> bool:
    total_price = 0
    for upgrade in combo:
        total_price += upgrade.price
        if upgrade.is_expired:
            logger.info(f"{bot.session_name} "
                        f"| Can't upgrade <e>{upgrade.name}</e> for daily combo "
                        f"| It's expired")
            return False
        if not upgrade.is_available:
            logger.info(f"{bot.session_name} "
                        f"| Can't upgrade <e>{upgrade.name}</e> for daily combo "
                        f"| Required condition: <e>{upgrade.condition}</e>")
            return False
        if upgrade.level > upgrade.max_level:
            logger.info(f"{bot.session_name} "
                        f"| Can't upgrade <e>{upgrade.name}</e> for daily combo "
                        f"| Because max level reached")
            return False
    seconds_to_combo_end = max(end_combo_timestamp - time(), 0)
    max_possible_balance = bot.profile.get_spending_balance() + bot.profile.earn_per_sec * seconds_to_combo_end
    if max_possible_balance < total_price:
        logger.info(f"{bot.session_name} "
                    f"| Impossible to buy daily combo "
                    f"| Total price of combo: {format_number(total_price)} "
                    f"| Max possible balance before combo end: {format_number(max_possible_balance)}")
        return False
    return True
