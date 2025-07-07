# jira.py

import os
import requests
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

AUTH_URL = "https://auth.atlassian.com/authorize"
TOKEN_URL = "https://auth.atlassian.com/oauth/token"
API_BASE = "https://api.atlassian.com"

SCOPES = [
    "read:jira-user",
    "read:jira-work",
    "write:jira-work",
    "manage:jira-configuration",
    "read:project:jira"
]

def get_authorization_url():
    client_id = os.getenv("JIRA_CLIENT_ID")
    redirect_uri = os.getenv("JIRA_REDIRECT_URI")
    scope_str = " ".join(SCOPES)

    params = {
        "audience": "api.atlassian.com",
        "client_id": client_id,
        "scope": scope_str,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "prompt": "consent",
        "state": "static_user_state"
    }

    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code):
    payload = {
        "grant_type": "authorization_code",
        "client_id": os.getenv("JIRA_CLIENT_ID"),
        "client_secret": os.getenv("JIRA_CLIENT_SECRET"),
        "code": code,
        "redirect_uri": os.getenv("JIRA_REDIRECT_URI"),
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, data=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def get_cloud_id(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{API_BASE}/oauth/token/accessible-resources"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    resources = response.json()
    if not resources:
        raise Exception("No accessible Jira cloud resources found.")
    return resources[0]["id"]

def get_all_projects(access_token, cloud_id):
    url = f"{API_BASE}/ex/jira/{cloud_id}/rest/api/3/project/search"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("values", [])

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
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}]
                }]
            },
            "issuetype": {"name": "Task"},
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code >= 400:
        raise Exception(f"{response.status_code} {response.reason}: {response.text}")
    return response.json()
