"""
Dorar Translator Bot (Session-Free Version)
--------------------------------------------
Ke sostu Telegram channelochi (dorarnet_telegram, almunajjid, ArIslamway)
addis post seyimeta, wede Amarigna yiteregmal, wede @ibnuabbas_hara
yiletefal.

Yihe version session string weyis computer AYFELEGM.
Manew yemiserew: yehulu public Telegram channel yalew free preview
gets (https://t.me/s/CHANNELNAME) beteqmo posts inaneb'aleN -
account login malefeleg silezih.

Yefelegut neger: TARGET_BOT_TOKEN bicha (ke @BotFather yalut).
"""

import os
import json
import time
import random
import logging
import re
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

BOT_TOKEN = os.environ["TARGET_BOT_TOKEN"]
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL", "@ibnuabbas_hara")

SOURCE_CHANNELS = [
    "dorarnet_telegram",
    "almunajjid",
    "ArIslamway",
]

STATE_FILE = "last_seen.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("dorar-translator")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {ch: 0 for ch in SOURCE_CHANNELS}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def fetch_channel_posts(channel: str):
    """Returns list of (message_id, text) tuples from the public t.me/s/ page."""
    url = f"https://t.me/s/{channel}"
    resp = requests.get(url, timeout=15, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    posts = []
    for wrap in soup.select("div.tgme_widget_message_wrap"):
        msg_div = wrap.select_one("div.tgme_widget_message")
        if not msg_div:
            continue
        data_post = msg_div.get("data-post", "")
        match = re.search(r"/(\d+)$", data_post)
        if not match:
            continue
        msg_id = int(match.group(1))

        text_div = msg_div.select_one("div.tgme_widget_message_text")
        text = text_div.get_text(separator="\n").strip() if text_div else ""

        posts.append((msg_id, text))

    posts.sort(key=lambda p: p[0])
    return posts


ERROR_PAGE_MARKERS = (
    "Error 500", "Server Error", "That's an error",
    "That’s an error", "please try again later",
)


def _looks_like_error_page(text: str) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in ERROR_PAGE_MARKERS)


def translate_to_amharic(text: str) -> str:
    if not text or not text.strip():
        return ""

    translator = GoogleTranslator(source="auto", target="am")
    chunks = [text[i:i + 4500] for i in range(0, len(text), 4500)]

    translated_chunks = []
    for chunk in chunks:
        translated = None
        for attempt in range(3):
            try:
                result = translator.translate(chunk)
                if result and not _looks_like_error_page(result):
                    translated = result
                    break
                log.warning("Translate attempt %d looked like an error page, retrying...", attempt + 1)
            except Exception as e:
                log.warning("Translate attempt %d failed: %s", attempt + 1, e)
            time.sleep(5 * (attempt + 1))

        if translated is None:
            raise RuntimeError("Translation failed after retries (likely rate-limited)")

        translated_chunks.append(translated)
        time.sleep(2)

    return "".join(translated_chunks)


def post_to_telegram(text: str):
    if not text.strip():
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(url, data={
        "chat_id": TARGET_CHANNEL,
        "text": text,
    })
    if resp.status_code != 200:
        log.error("Post failed: %s - %s", resp.status_code, resp.text)
    else:
        log.info("Posted translated message successfully.")


def check_channel(channel: str, last_id: int) -> int:
    new_last_id = last_id
    try:
        posts = fetch_channel_posts(channel)
    except Exception as e:
        log.error("Error fetching channel %s: %s", channel, e)
        return last_id

    for msg_id, text in posts:
        if msg_id <= last_id:
            continue
        if text.strip():
            try:
                translated = translate_to_amharic(text)
                post_to_telegram(translated)
                time.sleep(3)
            except Exception as e:
                log.error("Error translating/posting message %s from %s: %s "
                          "(will retry this one next cycle)", msg_id, channel, e)
                break
        new_last_id = max(new_last_id, msg_id)

    return new_last_id


def initialize_baseline(state):
    """On very first run (no state file yet), skip the backlog: mark each
    channel's current newest post as 'already seen' so we only translate
    genuinely NEW posts going forward, instead of flooding Google Translate
    with dozens of requests at once and getting blocked."""
    changed = False
    for channel in SOURCE_CHANNELS:
        if state.get(channel, 0) == 0:
            try:
                posts = fetch_channel_posts(channel)
                if posts:
                    state[channel] = posts[-1][0]
                    changed = True
                    log.info("Baseline set for %s at post id %d", channel, posts[-1][0])
            except Exception as e:
                log.error("Could not set baseline for %s: %s", channel, e)
    if changed:
        save_state(state)
    return state


def main():
    state = load_state()
    state = initialize_baseline(state)
    log.info("Bot started. Checking every 5-15 minutes.")

    while True:
        for channel in SOURCE_CHANNELS:
            last_id = state.get(channel, 0)
            new_last_id = check_channel(channel, last_id)
            if new_last_id != last_id:
                state[channel] = new_last_id
                save_state(state)

        sleep_for = random.randint(5 * 60, 15 * 60)
        log.info("Sleeping for %d seconds before next check.", sleep_for)
        time.sleep(sleep_for)


if __name__ == "__main__":
    main()
