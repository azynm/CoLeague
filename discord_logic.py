import requests
from datetime import datetime, timedelta

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