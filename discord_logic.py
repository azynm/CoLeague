import requests

def fetch_latest_messages(channel_id, headers):
    #Fetch messages from a channel
    r = requests.get(f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=20", headers=headers)
    if r.status_code == 200:
        data = r.json()
        messages = [f"<b>{m['author']['username']}</b>: {m['content']}" for m in data]
        return messages
    else:
        return f"Failed to fetch messages. Error: {r.text}"