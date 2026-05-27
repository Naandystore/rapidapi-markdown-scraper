import os
import json
import datetime
import subprocess

BIRTH_CERTIFICATE_PATH = "birth_certificate.json"

# --- MODEL TEMPLATE 1: SCRAPE TO MARKDOWN ---
TEMPLATE_SCRAPER = """import os
import requests
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from bs4 import BeautifulSoup
import markdownify

app = FastAPI(
    title="Scrape-to-Markdown API",
    description="Clean HTML scraping and conversion to LLM-ready markdown.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAPIDAPI_PROXY_SECRET = os.getenv("RAPIDAPI_PROXY_SECRET")

def verify_rapidapi_request(x_rapidapi_proxy_secret: str = Header(None)):
    if RAPIDAPI_PROXY_SECRET and x_rapidapi_proxy_secret != RAPIDAPI_PROXY_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized.")

class ScrapeRequest(BaseModel):
    url: HttpUrl
    include_raw_html: bool = False

@app.get("/")
def read_root():
    return {"status": "online", "model": "Scrape-to-Markdown API"}

@app.post("/scrape", dependencies=[Depends(verify_rapidapi_request)])
def scrape_url(payload: ScrapeRequest):
    target_url = str(payload.url)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string.strip() if soup.title else "Untitled Page"
    
    for tag in soup(["script", "style", "nav", "footer", "header", "iframe", "svg"]):
        tag.decompose()
        
    main_content = soup.find("main") or soup.find("article") or soup.find("body") or soup
    markdown_content = markdownify.markdownify(str(main_content), heading_style="ATX").strip()
    
    return {"title": title, "url": target_url, "markdown": markdown_content}
"""

# --- MODEL TEMPLATE 2: TEXT SUMMARIZER AND KEYWORD EXTRACTOR ---
TEMPLATE_SUMMARIZER = """import os
import re
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, constr

app = FastAPI(
    title="Text Summarizer and Keyword Extractor API",
    description="Lightweight NLP API for sentence ranking and keyword parsing.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAPIDAPI_PROXY_SECRET = os.getenv("RAPIDAPI_PROXY_SECRET")

def verify_rapidapi_request(x_rapidapi_proxy_secret: str = Header(None)):
    if RAPIDAPI_PROXY_SECRET and x_rapidapi_proxy_secret != RAPIDAPI_PROXY_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized.")

class SummarizeRequest(BaseModel):
    text: constr(min_length=100, max_length=15000)
    summary_sentences_count: int = 3

@app.get("/")
def read_root():
    return {"status": "online", "model": "Text Summarizer & Keyword API"}

@app.post("/summarize", dependencies=[Depends(verify_rapidapi_request)])
def summarize_text(payload: SummarizeRequest):
    text = payload.text
    num_sentences = payload.summary_sentences_count
    
    # 1. Clean and tokenize words to extract keywords
    words = re.findall(r'\\w+', text.lower())
    stopwords = {"the", "and", "a", "of", "to", "is", "in", "it", "that", "you", "he", "was", "for", "on", "are", "as", "with", "his", "they", "i", "at", "be", "this", "have", "from", "or", "one", "had", "by", "word", "but", "not", "what", "all", "were", "we", "when", "your", "can", "said", "there", "use", "an", "each", "which", "she", "do", "how", "their", "if"}
    
    word_frequencies = {}
    for word in words:
        if word not in stopwords and len(word) > 2:
            word_frequencies[word] = word_frequencies.get(word, 0) + 1
            
    if not word_frequencies:
        raise HTTPException(status_code=400, detail="Text too short or lacks content.")
        
    # Get top keywords
    sorted_keywords = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)[:7]
    keywords = [kw[0] for kw in sorted_keywords]
    
    # Max word frequency to normalize scores
    max_freq = max(word_frequencies.values())
    for word in word_frequencies:
        word_frequencies[word] = word_frequencies[word] / max_freq
        
    # 2. Tokenize sentences
    sentences = re.split(r'(?<=[.!?])\\s+', text)
    sentence_scores = {}
    for sent in sentences:
        sent_clean = sent.lower()
        for word in word_frequencies:
            if word in sent_clean:
                sentence_scores[sent] = sentence_scores.get(sent, 0) + word_frequencies[word]
                
    # Sort and pick top sentences in order of appearance
    top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_sentences]
    summary_list = [s[0] for s in top_sentences]
    
    # Re-order to match original text sequence
    ordered_summary = [s for s in sentences if s in summary_list]
    
    return {
        "summary": " ".join(ordered_summary),
        "keywords": keywords,
        "word_count": len(words),
        "sentence_count": len(sentences)
    }
"""

# --- MODEL TEMPLATE 3: READABILITY EXTRACTOR API ---
TEMPLATE_READABILITY = """import os
import requests
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from bs4 import BeautifulSoup

app = FastAPI(
    title="Readability Extractor API",
    description="Clean main text and estimate reading metrics from web pages.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAPIDAPI_PROXY_SECRET = os.getenv("RAPIDAPI_PROXY_SECRET")

def verify_rapidapi_request(x_rapidapi_proxy_secret: str = Header(None)):
    if RAPIDAPI_PROXY_SECRET and x_rapidapi_proxy_secret != RAPIDAPI_PROXY_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized.")

class ReadabilityRequest(BaseModel):
    url: HttpUrl

@app.get("/")
def read_root():
    return {"status": "online", "model": "Readability Extractor API"}

@app.post("/readability", dependencies=[Depends(verify_rapidapi_request)])
def extract_readability(payload: ReadabilityRequest):
    target_url = str(payload.url)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string.strip() if soup.title else "Untitled Article"
    
    # Strip garbage
    for tag in soup(["script", "style", "nav", "footer", "header", "iframe", "svg", "form", "aside"]):
        tag.decompose()
        
    # Extract clean text from paragraphs
    paragraphs = soup.find_all("p")
    text_content = "\\n\\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20])
    
    words = text_content.split()
    word_count = len(words)
    reading_time_mins = max(1, round(word_count / 225)) # Avg reading speed 225 wpm
    
    return {
        "title": title,
        "clean_text": text_content,
        "word_count": word_count,
        "reading_time_minutes": reading_time_mins
    }
"""

CATALOG = [
    {"name": "Scrape-to-Markdown API", "code": TEMPLATE_SCRAPER},
    {"name": "Text Summarizer and Keyword Extractor API", "code": TEMPLATE_SUMMARIZER},
    {"name": "Readability Extractor API", "code": TEMPLATE_READABILITY}
]

def git_commit_and_push(new_model_name):
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO") # Format: username/repo-name
    
    if not github_token or not github_repo:
        print("[GIT] GITHUB_TOKEN or GITHUB_REPO not set. Skipping autonomous push.")
        print("[GIT] User action required: please commit and push changes manually.")
        return False
        
    try:
        # Configure git locally
        subprocess.run(["git", "config", "user.name", "Autonomous Pivot Bot"], check=True)
        subprocess.run(["git", "config", "user.email", "bot@antigravity-ai.com"], check=True)
        
        # Add files
        subprocess.run(["git", "add", "main.py", BIRTH_CERTIFICATE_PATH], check=True)
        
        # Commit
        commit_msg = f"Autonomous Pivot: Switched API to {new_model_name} due to profitability timeout."
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        
        # Push back using authentication token
        remote_url = f"https://{github_token}@github.com/{github_repo}.git"
        subprocess.run(["git", "push", remote_url, "main"], check=True)
        print("[GIT] Code successfully pushed to GitHub! Render redeployment triggered.")
        return True
    except Exception as e:
        print(f"[GIT ERROR] Failed to commit or push: {str(e)}")
        return False

def main():
    if not os.path.exists(BIRTH_CERTIFICATE_PATH):
        print(f"[ERROR] {BIRTH_CERTIFICATE_PATH} not found. Running initialization first.")
        return

    with open(BIRTH_CERTIFICATE_PATH, "r") as f:
        cert = json.load(f)
        
    current_name = cert["model_name"]
    print(f"Current Model: {current_name}")
    
    # Find next index in Catalog
    current_index = 0
    for idx, item in enumerate(CATALOG):
        if item["name"] == current_name:
            current_index = idx
            break
            
    next_index = (current_index + 1) % len(CATALOG)
    next_model = CATALOG[next_index]
    
    print(f"Pivoting to next service: {next_model['name']}")
    
    # Overwrite main.py with the new API implementation
    with open("main.py", "w") as f:
        f.write(next_model["code"])
    print("Rewrote main.py with the new API codebase.")
    
    # Update birth certificate
    cert["model_name"] = next_model["name"]
    cert["start_date"] = datetime.date.today().isoformat()
    cert["last_check"] = datetime.date.today().isoformat()
    
    with open(BIRTH_CERTIFICATE_PATH, "w") as f:
        json.dump(cert, f, indent=4)
    print("Updated birth certificate with the new model details.")
    
    # Git sync
    git_commit_and_push(next_model["name"])

if __name__ == "__main__":
    main()
