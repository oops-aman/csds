import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GITHUB_API_URL = "https://api.github.com"
ORG_NAME = "your-org-name"  # Replace with your organization name
TOKEN = "your-github-token"  # Replace with your GitHub token

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_org_members(org_name):
    url = f"{GITHUB_API_URL}/orgs/{org_name}/members"
    members = []
    page = 1
    while True:
        resp = requests.get(url, headers=HEADERS, params={"per_page": 100, "page": page}, verify=False)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        members.extend([user["login"] for user in data])
        page += 1
    return members

def get_org_repos(org_name):
    url = f"{GITHUB_API_URL}/orgs/{org_name}/repos"
    repos = []
    page = 1
    while True:
        resp = requests.get(url, headers=HEADERS, params={"per_page": 100, "page": page}, verify=False)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        repos.extend([repo["name"] for repo in data])
        page += 1
    return repos

def get_user_commits(org_name, repo, username):
    url = f"{GITHUB_API_URL}/repos/{org_name}/{repo}/commits"
    resp = requests.get(url, headers=HEADERS, params={"author": username, "per_page": 100}, verify=False)
    resp.raise_for_status()
    commits = resp.json()
    files = set()
    for commit in commits:
        sha = commit.get("sha")
        if sha:
            commit_url = f"{GITHUB_API_URL}/repos/{org_name}/{repo}/commits/{sha}"
            commit_resp = requests.get(commit_url, headers=HEADERS, verify=False)
            commit_resp.raise_for_status()
            commit_data = commit_resp.json()
            for f in commit_data.get("files", []):
                files.add(f["filename"])
    return list(files)

def get_user_pull_requests(org_name, repo, username):
    url = f"{GITHUB_API_URL}/repos/{org_name}/{repo}/pulls"
    prs = []
    page = 1
    files = set()
    while True:
        resp = requests.get(url, headers=HEADERS, params={"state": "all", "per_page": 100, "page": page}, verify=False)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        user_prs = [pr for pr in data if pr["user"]["login"] == username]
        for pr in user_prs:
            pr_number = pr.get("number")
            if pr_number:
                pr_url = f"{GITHUB_API_URL}/repos/{org_name}/{repo}/pulls/{pr_number}/files"
                pr_files_resp = requests.get(pr_url, headers=HEADERS, verify=False)
                pr_files_resp.raise_for_status()
                pr_files = pr_files_resp.json()
                for f in pr_files:
                    files.add(f["filename"])
        prs.extend(user_prs)
        page += 1
    return list(files)

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python github_data.py <github-username>")
        sys.exit(1)
    username = sys.argv[1]
    repos = get_org_repos(ORG_NAME)
    print(f"Analyzing user: {username}")
    for repo in repos:
        commit_files = get_user_commits(ORG_NAME, repo, username)
        pr_files = get_user_pull_requests(ORG_NAME, repo, username)
        all_files = set(commit_files) | set(pr_files)
        if all_files:
            print(f"  Repo: {repo} - Files changed by {username}:")
            for f in sorted(all_files):
                print(f"    {f}")

if __name__ == "__main__":
    main()