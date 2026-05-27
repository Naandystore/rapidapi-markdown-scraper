import os
import requests
import subprocess
from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from bs4 import BeautifulSoup
import markdownify

app = FastAPI(
    title="Web Page Scraper to Markdown API",
    description="Clean HTML scraping and conversion to LLM-ready markdown.",
    version="1.0.0"
)

# Enable CORS for public developer access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional RapidAPI proxy secret to prevent users from bypassing our paywall.
# If configured on Render, we will verify this secret header.
RAPIDAPI_PROXY_SECRET = os.getenv("RAPIDAPI_PROXY_SECRET")

def verify_rapidapi_request(x_rapidapi_proxy_secret: str = Header(None)):
    if RAPIDAPI_PROXY_SECRET and x_rapidapi_proxy_secret != RAPIDAPI_PROXY_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized request. Access must be routed through RapidAPI."
        )

class ScrapeRequest(BaseModel):
    url: HttpUrl
    include_raw_html: bool = False

def run_profit_check_script():
    try:
        # Run check_profit.py script as a background process
        subprocess.run(["python", "check_profit.py"], check=True)
    except Exception as e:
        print(f"[CRON TRIGGER ERROR] Failed to run check_profit.py: {str(e)}")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Web Page Scraper to Markdown API",
        "description": "Convert web pages to clean Markdown optimized for LLM consumption.",
        "usage": "POST to /scrape with JSON body {'url': 'https://example.com'}"
    }

@app.post("/scrape", dependencies=[Depends(verify_rapidapi_request)])
def scrape_url(payload: ScrapeRequest):
    target_url = str(payload.url)
    
    # Fake user agent to bypass basic scraper blockades
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to retrieve URL content: {str(e)}"
        )
    
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Extract page title
    title = soup.title.string.strip() if soup.title else "Untitled Page"
    
    # Clean the HTML to get rid of boilerplate noise (ads, navs, footer, etc.)
    tags_to_remove = [
        "script", "style", "nav", "footer", "header", "form", 
        "iframe", "noscript", "svg", "button", "input"
    ]
    for tag in soup(tags_to_remove):
        tag.decompose()
        
    # Attempt to isolate main content (articles, main tags, or main body container)
    main_content = soup.find("main") or soup.find("article") or soup.find("body") or soup
    
    # Convert cleaned HTML to clean Markdown
    markdown_content = markdownify.markdownify(
        str(main_content),
        heading_style="ATX"
    ).strip()
    
    response_data = {
        "title": title,
        "url": target_url,
        "markdown": markdown_content
    }
    
    if payload.include_raw_html:
        response_data["raw_html"] = str(main_content)
        
    return response_data

@app.post("/trigger-profit-check")
def trigger_profit_check(background_tasks: BackgroundTasks, x_secret_trigger_key: str = Header(None)):
    # Verify trigger key matches the proxy secret to secure this endpoint
    if RAPIDAPI_PROXY_SECRET and x_secret_trigger_key != RAPIDAPI_PROXY_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized trigger key."
        )
    
    # Queue the profit check script execution
    background_tasks.add_task(run_profit_check_script)
    return {"status": "triggered"}
