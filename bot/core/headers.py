# pylint: disable=C0301
import json as json_parser

from bot.config import API_HOST, BASE_URL


def create_hamster_headers(json: dict | None) -> dict:
    return create_headers(
        json=json,
        host=API_HOST,
        origin=BASE_URL
    )


def create_headers(json: dict | None, host: str, origin: str) -> dict:
    headers = {
        'Accept-Language': 'en-GB,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Host': host,
        'Origin': origin,
        'Referer': f"{origin}/",
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
    }
    if json is None:
        headers.update({
            'Accept': '*/*',
            'Content-Length': "0",
        })
    else:
        headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Content-Length': str(len(json_parser.dumps(json).encode('utf-8'))),
        })
    return headers
