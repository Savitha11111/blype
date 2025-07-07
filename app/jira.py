# app/jira.py

import os
import requests

AUTH_URL = "https://auth.atlassian.com/authorize"
TOKEN_URL = "https://auth.atlassian.com/oauth/token"
API_BASE = "https://api.atlassian.com"

SCOPES = [
    "read:jira-user",
    "read:jira-work",
    "write:jira-work"
]

def get_authorization_url():
    client_id = os.getenv("JIRA_CLIENT_ID")
    redirect_uri = os.getenv("JIRA_REDIRECT_URI")
    scope = " ".join(SCOPES)
    return (
        f"{AUTH_URL}?"
        f"audience=api.atlassian.com&"
        f"client_id={client_id}&"
        f"scope={scope}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"prompt=consent"
    )

def exchange_code_for_token(code):
    data = {
        "grant_type": "authorization_code",
        "client_id": os.getenv("JIRA_CLIENT_ID"),
        "client_secret": os.getenv("JIRA_CLIENT_SECRET"),
        "code": code,
        "redirect_uri": os.getenv("JIRA_REDIRECT_URI"),
    }
    response = requests.post(TOKEN_URL, json=data)
    response.raise_for_status()
    return response.json()

def get_cloud_id(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"{API_BASE}/oauth/token/accessible-resources", headers=headers)
    r.raise_for_status()
    return r.json()[0]["id"]

def create_jira_issue(access_token, cloud_id, project_key, summary, description):
    url = f"{API_BASE}/ex/jira/{cloud_id}/rest/api/3/issue"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Task"},
        }
    }
    r = requests.post(url, json=payload, headers=headers)
    r.raise_for_status()
    return r.json()
