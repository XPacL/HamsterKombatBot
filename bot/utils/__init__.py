from .logger import logger


def format_number(num):
    negative = False
    if num < 0:
        negative = True
        num = abs(num)
    if num >= 1_000_000_000:
        formatted_num = f'{num / 1_000_000_000:.2f}B'
    elif num >= 1_000_000:
        formatted_num = f'{num / 1_000_000:.2f}M'
    elif num >= 1_000:
        formatted_num = f'{num / 1_000:.2f}k'
    else:
        formatted_num = str(num)
    if negative:
        return f'-{formatted_num}'
    else:
        return formatted_num

