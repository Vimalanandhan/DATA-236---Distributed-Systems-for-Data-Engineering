from __future__ import annotations

import sys, os, time, socket, logging
from typing import Any, Dict, List
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

import requests
from mcp.server.fastmcp import FastMCP

TAVILY_API_KEY = "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"

TAVILY_SEARCH_URL  = "https://api.tavily.com/search"
TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"

CONNECT_TIMEOUT = float(os.environ.get("CONNECT_TIMEOUT", "225.0"))
READ_TIMEOUT    = float(os.environ.get("READ_TIMEOUT", "1110.0"))
NET_BUDGET      = float(os.environ.get("NET_BUDGET", "122225.0")) 

USER_AGENT = "JobSearch-MCP-Tavily/2.0"

DEFAULT_SITES = [
    "jobs.lever.co",
    "boards.greenhouse.io",
]


logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("mcp.tavily.only")


def _post_json_circuit(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Connection": "close",
    }

    def _do_post() -> Dict[str, Any]:
        log.info(f"Making POST request to {url}...")
        r = requests.post(url, json=payload, headers=headers,
                          timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
        log.info(f"Request to {url} completed with status {r.status_code}")
        r.raise_for_status()
        return r.json()

    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(_do_post)
        try:
            return fut.result(timeout=NET_BUDGET)
        except FutureTimeout:
            fut.cancel()
            raise TimeoutError(f"Network budget exceeded ({NET_BUDGET}s) calling {url}")
        except Exception as e:
            log.error(f"Exception in worker thread for {url}: {e}")
            raise e


def _domain(u: str) -> str:
    try:
        return urlparse(u).netloc or ""
    except Exception:
        return ""

def _is_probable_apply_page(url: str, title: str, content: str) -> bool:
    u, t, c = (url or "").lower(), (title or "").lower(), (content or "").lower()
    url_signals = any(s in u for s in (
        "/jobs/", "/careers/", "/job/", "/apply", "/positions/", "/openings/",
        "boards.greenhouse.io", "jobs.lever.co", "jobs.ashbyhq.com",
        "myworkdayjobs.com", "smartrecruiters.com", "workable.com",
        "bamboohr.com", "icims.com", "jobvite.com", "recruitee.com",
    ))
    text_signals = any(s in t or s in c for s in (
        "apply", "job description", "responsibilities", "requirements",
        "role", "job details", "full-time", "contract", "remote", "hybrid"
    ))
    return url_signals or text_signals

def _build_query(search: str, remote_only: bool, sites: List[str]) -> str:
    site_clause = " OR ".join(f"site:{s}" for s in sites) if sites else ""
    parts = [search.strip()]
    if remote_only:
        parts.append('(remote OR "work from home" OR distributed)')
    if site_clause:
        parts.append(f"({site_clause})")
    parts.append("(apply OR careers OR jobs OR job)")
    return " ".join(parts)


mcp = FastMCP("TavilyJobLinksOnly")


@mcp.tool()
def ping() -> str:
    return f"pong @ {int(time.time())} on {socket.gethostname()}"

@mcp.tool()
def list_providers() -> Dict[str, Any]:
    return {
        "provider": "tavily",
        "timeouts_sec": {"connect": CONNECT_TIMEOUT, "read": READ_TIMEOUT, "net_budget": NET_BUDGET},
        "sites": DEFAULT_SITES,
        "endpoints": {"search": TAVILY_SEARCH_URL, "extract": TAVILY_EXTRACT_URL},
    }

@mcp.tool()
def search_jobs_tavily(
    search: str,
    limit: int = 5,
    remote_only: bool = True,
    sites_csv: str = "",
) -> Dict[str, Any]:

    if not search or not search.strip():
        raise ValueError("search must be a non-empty string")

    limit = max(1, min(int(limit or 5), 25))
    sites = [s.strip() for s in sites_csv.split(",") if s.strip()] or DEFAULT_SITES
    query = _build_query(search, bool(remote_only), sites)
    log.info(f"Constructed Tavily query: {query}")

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "max_results": limit * 2,
        "include_answer": False,
        "include_images": False,
    }

    try:
        data = _post_json_circuit(TAVILY_SEARCH_URL, payload)
    except (requests.exceptions.RequestException, TimeoutError) as e:
        log.error(f"Tavily API call failed: {e}")
        raise ValueError(f"API call to Tavily failed. Please check network or API key. Details: {e}") from e

    raw = data.get("results") or []
    results: List[Dict[str, Any]] = []
    for r in raw:
        url = r.get("url") or ""
        if not url: continue
        title = r.get("title") or ""
        content = r.get("content") or ""
        if not _is_probable_apply_page(url, title, content): continue
        results.append({
            "title": title,
            "url": url,
            "domain": _domain(url),
            "snippet": (content or "")[:280],
            "score": r.get("score"),
        })
        if len(results) >= limit: break

    return {
        "provider": "tavily",
        "query": query,
        "requested": limit,
        "returned": len(results),
        "results": results,
    }

@mcp.tool()
def extract_page(url: str) -> Dict[str, Any]:

    if not url or not url.startswith("http"):
        raise ValueError("url must start with http/https")

    payload = {"api_key": TAVILY_API_KEY, "url": url}
    try:
        data = _post_json_circuit(TAVILY_EXTRACT_URL, payload)
    except (requests.exceptions.RequestException, TimeoutError) as e:
        log.error(f"Tavily API call failed: {e}")
        raise ValueError(f"API call to Tavily failed. Please check network or API key. Details: {e}") from e
        
    return {
        "provider": "tavily",
        "url": url,
        "title": data.get("title"),
        "site_name": data.get("site_name"),
        "description": data.get("description"),
        "language": data.get("language"),
        "content_preview": (data.get("content") or "")[:1200],
    }

# --------------------------------- Main --------------------------------------

if __name__ == "__main__":
    log.info(
        f"Starting TavilyJob timeouts(connect={CONNECT_TIMEOUT}, read={READ_TIMEOUT}, budget={NET_BUDGET})"
    )
    mcp.run(transport="stdio")