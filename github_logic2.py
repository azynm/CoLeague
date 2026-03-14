import requests

def get_detailed_github_data(repo, headers):
    base_url = f"https://api.github.com/repos/{repo}"
    out = []

    # 1. Get Commits (includes Author, Date, Message)
    commits_res = requests.get(f"{base_url}/commits", headers=headers)
    if commits_res.status_code == 200:
        for c in commits_res.json():
            out.append({
                "type": "commit/merge",
                "author": c['commit']['author']['name'],
                "date": c['commit']['author']['date'],
                "message": c['commit']['message'],
                "sha": c['sha']
            })

    # 2. Get Pull Requests (This is where "Approvals" and "Branches" live)
    # We use state=closed to find merged PRs
    prs_res = requests.get(f"{base_url}/pulls?state=closed", headers=headers)
    if prs_res.status_code == 200:
        for pr in prs_res.json():
            if pr.get('merged_at'): # Only look at successfully merged PRs
                
                # Fetch Approvers for this specific PR
                reviews_res = requests.get(f"{base_url}/pulls/{pr['number']}/reviews", headers=headers)
                approvers = [r['user']['login'] for r in reviews_res.json() if r['state'] == 'APPROVED']
                
                out.append({
                    "type": "merge_request",
                    "id": pr['number'],
                    "title": pr['title'],
                    "author": pr['user']['login'],
                    "merged_at": pr['merged_at'],
                    "source_branch": pr['head']['ref'],
                    "target_branch": pr['base']['ref'],
                    "approvers": approvers
                })

    return out