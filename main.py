import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

import json
import time
import subprocess
import requests
import re
from bs4 import BeautifulSoup
from googletrans import Translator

# Configuration
USERNAME = "ActuFoot_"
TELEGRAM_TOKEN = "8036416560:AAETLYeBRZe8w0bfpJujLNnJgG--kJqnsK8"
TELEGRAM_CHAT_ID = "5249034734"
SEEN_FILE = "seen.json"
CHECK_INTERVAL = 30  # en secondes

translator = Translator()

def clean_text(text):
    text = BeautifulSoup(text, "html.parser").get_text()
    text = re.sub(r"(NOUVEL ARTICLE|NEW ARTICLE)[\s:\-]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"http\S+", "", text)
    return text.strip()

def translate_text(text):
    try:
        return translator.translate(text, dest="fr").text
    except Exception as e:
        print(f"[!] Erreur de traduction : {e}")
        return text

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen_ids):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_ids), f)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def send_telegram_photo(image_url, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def extract_image_url(content):
    soup = BeautifulSoup(content, "html.parser")
    img = soup.find("img")
    if img and img.get("src"):
        return img["src"]
    return None

def fetch_latest_tweet():
    try:
        result = subprocess.run(
            ["snscrape", "--jsonl", f"twitter-user {USERNAME}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise Exception(result.stderr)
        lines = result.stdout.strip().split("\n")
        if lines:
            return json.loads(lines[0])
    except Exception as e:
        print(f"[!] Erreur récupération tweet : {e}")
    return None

def process_tweet(tweet, seen_ids):
    tweet_id = tweet["id"]
    if tweet_id in seen_ids:
        return

    raw_text = tweet.get("content", "")
    cleaned = clean_text(raw_text)
    translated = translate_text(cleaned)

    image_url = None
    if tweet.get("media"):
        for media in tweet["media"]:
            if media.get("type") == "photo":
                image_url = media.get("fullUrl")
                break

    if image_url:
        send_telegram_photo(image_url, translated)
    else:
        send_telegram_message(translated)

    seen_ids.add(tweet_id)
    save_seen(seen_ids)
    print(f"[+] Nouveau tweet envoyé : {translated[:60]}...")

def main():
    print("[*] Démarrage du bot avec snscrape...")
    seen_ids = load_seen()

    while True:
        try:
            tweet = fetch_latest_tweet()
            if tweet:
                process_tweet(tweet, seen_ids)
        except Exception as e:
            print(f"[!] Erreur dans la boucle principale : {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
