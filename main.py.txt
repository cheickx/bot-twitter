import snscrape.modules.twitter as sntwitter
import time
import json
import re
import requests
from googletrans import Translator
from bs4 import BeautifulSoup

# === CONFIGURATION ===
USERNAME = "ActuFoot_"  # Compte Twitter à surveiller
TELEGRAM_TOKEN = "8036416560:AAETLYeBRZe8w0bfpJujLNnJgG--kJqnsK8"
TELEGRAM_CHAT_ID = "5249034734"
SEEN_FILE = "seen.json"
CHECK_INTERVAL = 30  # secondes

translator = Translator()

# === UTILITAIRES ===
def clean_text(text):
    text = BeautifulSoup(text, "html.parser").get_text()
    text = re.sub(r"(NOUVEL ARTICLE|NEW ARTICLE)[\s:\-]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"http\S+", "", text)
    return text.strip()

def translate_text(text):
    try:
        return translator.translate(text, dest='fr').text
    except Exception as e:
        print(f"[!] Erreur de traduction : {e}")
        return text

def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    except FileNotFoundError:
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

def process_tweet(tweet, seen_ids):
    if tweet.id in seen_ids:
        return

    cleaned = clean_text(tweet.content)
    translated = translate_text(cleaned)

    # Image si disponible
    image_url = None
    if tweet.media:
        for media in tweet.media:
            if hasattr(media, 'fullUrl'):
                image_url = media.fullUrl
                break

    if image_url:
        send_telegram_photo(image_url, translated)
    else:
        send_telegram_message(translated)

    seen_ids.add(tweet.id)
    save_seen(seen_ids)
    print(f"[+] Tweet envoyé : {translated[:60]}...")

# === BOUCLE PRINCIPALE ===
def main():
    seen_ids = load_seen()
    print("[*] Démarrage du bot avec snscrape...")

    while True:
        try:
            tweets = list(sntwitter.TwitterUserScraper(USERNAME).get_items())
            if tweets:
                for tweet in reversed(tweets[:5]):  # Vérifie les 5 derniers tweets
                    process_tweet(tweet, seen_ids)
        except Exception as e:
            print(f"[!] Erreur dans la boucle principale : {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
