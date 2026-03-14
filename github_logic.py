import requests

def get_github_data(repo, headers):
    endpoints = ["/commits", "/branches", "/issues?state=all"]
    
	#Loops through all endpoints to collect the data
    out = []
	for e in endpoints:
        r = requests.get(f"https://api.github.com/repos/{repo}{e}", headers=headers)
        if r.status_code == 200:
        	data = r.json()
            for item in data:
				if e == "/commits":
                    if "Merge" in item["commit"]["message"]:
						out.append({"type":"merge", })
					else:
						out.append({"type":"commit", })
				elif e == "/branches":
					out.append({"type":"branch", })
				elif e == "/issues?state=all":
					out.append({"type":"issues", })

    # Normalize different API responses into one format for the template
    for item in raw_data[:10]: # Limit to last 10
        if view == "branches":
            formatted.append({"title": f"Branch: {item['name']}", "user": "System", "date": "N/A"})
        elif view == "issues":
            formatted.append({"title": f"#{item['number']} {item['title']}", "user": item['user']['login'], "date": item['created_at']})
        else: # Commits / Merges
            msg = item['commit']['message']
            is_merge = "Merge" in msg
            formatted.append({
                "title": f"{'[MERGE] ' if is_merge else ''}{msg.splitlines()[0]}",
                "user": item['commit']['author']['name'],
                "date": item['commit']['author']['date']
            })
    return formatted