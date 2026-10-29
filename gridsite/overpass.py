"""Small Overpass API client with retries and mirror fallback."""

import time

import requests

from .config import OVERPASS_URLS, USER_AGENT


def run_query(query: str, retries: int = 3, timeout: int = 180) -> dict:
    """POST a query to Overpass and return the parsed JSON.

    Tries each mirror in turn and backs off between attempts, since the
    public endpoints rate-limit and occasionally return empty bodies.
    """
    last_error = None
    for attempt in range(retries):
        for url in OVERPASS_URLS:
            try:
                resp = requests.post(
                    url,
                    data={"data": query},
                    headers={"User-Agent": USER_AGENT},
                    timeout=timeout,
                )
                resp.raise_for_status()
                return resp.json()
            except (requests.RequestException, ValueError) as err:
                last_error = err
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Overpass query failed after {retries} attempts: {last_error}")


def bbox_str(bbox: tuple) -> str:
    south, west, north, east = bbox
    return f"{south},{west},{north},{east}"
