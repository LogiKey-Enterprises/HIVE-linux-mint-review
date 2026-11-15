from __future__ import annotations
import json, os, urllib.parse, urllib.request
from .repositories import add_repository
API="https://api.github.com/search/repositories"

def search_github(query: str, limit: int = 10) -> list[dict]:
    if not query.strip(): raise ValueError("Search query cannot be empty")
    params=urllib.parse.urlencode({"q":query,"sort":"stars","order":"desc","per_page":min(max(limit,1),30)})
    headers={"Accept":"application/vnd.github+json","User-Agent":"HIVE-Engine/0.1"}
    if os.environ.get("GITHUB_TOKEN"): headers["Authorization"]=f"Bearer {os.environ['GITHUB_TOKEN']}"
    req=urllib.request.Request(f"{API}?{params}",headers=headers)
    with urllib.request.urlopen(req,timeout=20) as response:
        payload=json.loads(response.read().decode("utf-8"))
    saved=[]
    for item in payload.get("items",[]):
        rid=add_repository(item["html_url"],description=item.get("description"),
            language=item.get("language"),stars=item.get("stargazers_count"),
            forks=item.get("forks_count"),default_branch=item.get("default_branch"))
        saved.append({"id":rid,"full_name":item["full_name"],"description":item.get("description"),
          "language":item.get("language"),"stars":item.get("stargazers_count"),"url":item["html_url"]})
    return saved
