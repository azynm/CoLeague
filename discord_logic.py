import os
import time
import requests
from datetime import datetime, timedelta

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_all_messages(dashboard_id, headers, last_time):
    #Fetch a list of all channels in the server
    r = requests.get(f"https://discord.com/api/v10/guilds/{dashboard_id}/channels", headers=headers)
    if r.status_code != 200:
        return f"Error: Could not fetch channels. Is the bot in the server? (Code: {r.status_code})"

    #Filter for text channels and scrape messages
    channels = r.json()
    text_channels = [c for c in channels if c['type'] == 0]
    out = []
    for c in text_channels:
        out.extend(fetch_latest_messages(c['id'], headers, last_time))
        
    return out

def fetch_latest_messages(channel_id, headers, since_datetime):
    #Get snowflake for most recent time
    after_id = datetime_to_snowflake(since_datetime)    
    all_messages = []
    
    #Loops to get 100 messages at a time
    while True:
        #Fetch latest messages from a channel
        r = requests.get(f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=100&after={after_id}", headers=headers)
        if r.status_code == 429:
            time.sleep(r.json().get('retry_after', 1))
            continue
        
        #Format data
        data = r.json()
        if not data:
            break 
        for m in data:
            all_messages.append({
                "author": m['author']['username'],
                "content": m['content'],
                "timestamp": m['timestamp'],
                "reactions": m.get('reactions', [])
            })

        #If this is the last page, break loop
        if len(data) < 100:
            break

        #Prepare for next loop
        after_id = data[0]['id'] 

    return all_messages
    
#Converts python datetime to snowflake
def datetime_to_snowflake(dt_obj):
    discord_epoch = 1420070400000
    timestamp_ms = int(dt_obj.timestamp() * 1000)
    snowflake = (timestamp_ms - discord_epoch) << 22
    return snowflake

def analyse_sentiment(messages):
    """
    Send a batch of Discord messages to Gemini and get an overall sentiment label.
    Returns one of: "positive", "neutral", "negative", "toxic", "highly toxic"
    """
    if not messages:
        return "neutral"

    conversation = "\n".join(f"{m['author']}: {m['content']}" for m in messages)

    prompt = f"""Classify the overall sentiment of these Discord messages into exactly one of these labels:
positive, neutral, negative, toxic, highly toxic

Messages:
{conversation}

Respond with ONLY the label, nothing else."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            label = data["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
            valid = {"positive", "neutral", "negative", "toxic", "highly toxic"}
            if label in valid:
                return label
            print(f"Gemini returned unexpected sentiment label: {label!r}, defaulting to neutral")
            return "neutral"
        except requests.exceptions.HTTPError:
            if response.status_code == 429:
                wait_time = 5 * (2 ** attempt)
                print(f"Sentiment rate limited (429). Retrying in {wait_time}s (Attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                print(f"Sentiment analysis failed: {response.status_code}")
                break
        except Exception as e:
            print(f"Sentiment analysis failed: {e}")
            break
    return "neutral"
