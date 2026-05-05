import streamlit as st
import requests
import os
import re
import random
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
from urllib.parse import urlparse, quote_plus

load_dotenv(override=True)

def get_secret(key):
    """Read from Streamlit secrets (cloud) or .env (local)."""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=get_secret("OPENROUTER_API_KEY")
)
SERPAPI_KEY = get_secret("SERPAPI_KEY")

# ─── Helpers ─────────────────────────────────────────────────────────────────
def get_headers():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
    ]
    return {
        "User-Agent": random.choice(agents),
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.google.com/",
    }

def extract_asin(url):
    match = re.search(r"/([A-Z0-9]{10})(?:[/?]|$)", url)
    return match.group(1) if match else None

def detect_source(url):
    if "amazon" in url:
        return "amazon"
    elif "flipkart" in url:
        return "flipkart"
    return "generic"

# ─── Strategy 1: SerpAPI Google search for Amazon product reviews ─────────────
def fetch_via_serpapi_amazon(asin):
    """Use Google via SerpAPI to find reviews for this ASIN."""
    if not SERPAPI_KEY or not asin:
        return None, "No SerpAPI key or ASIN"
    query = f"amazon {asin} customer reviews"
    try:
        res = requests.get("https://serpapi.com/search.json", params={
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 10
        }, timeout=15).json()
        snippets = []
        for r in res.get("organic_results", []):
            snippet = r.get("snippet", "")
            if snippet and len(snippet) > 40:
                snippets.append(f"- {snippet}")
        if snippets:
            return "\n".join(snippets[:20]), "Google → Amazon Reviews"
        error = res.get("error", "")
        if error:
            return None, f"SerpAPI error: {error}"
    except Exception as e:
        return None, str(e)
    return None, "No snippets found"

# ─── Strategy 2: SerpAPI Google search for reviews ───────────────────────────
def fetch_via_google_search(product_name_or_url):
    if not SERPAPI_KEY:
        return None, "No SerpAPI key"
    # Build a review-focused query
    query = f"{product_name_or_url} customer reviews site:amazon.in OR site:flipkart.com OR site:91mobiles.com OR site:smartprix.com"
    try:
        res = requests.get("https://serpapi.com/search.json", params={
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 10
        }, timeout=15).json()
        snippets = []
        for r in res.get("organic_results", []):
            snippet = r.get("snippet", "")
            if snippet and len(snippet) > 40:
                snippets.append(f"- {snippet}")
        if snippets:
            return "\n".join(snippets[:20]), "Google Search Snippets"
    except Exception as e:
        return None, str(e)
    return None, "No Google snippets found"

# ─── Strategy 3: Scrape 91mobiles / Smartprix / Notebookcheck (open sites) ───
def fetch_via_open_review_site(product_keyword):
    """Try 91mobiles user reviews - they don't block bots heavily."""
    try:
        search_url = f"https://www.91mobiles.com/search/?search={quote_plus(product_keyword)}"
        resp = requests.get(search_url, headers=get_headers(), timeout=12)
        soup = BeautifulSoup(resp.text, "lxml")
        # Try to find review text blocks
        reviews = soup.select(".user-review-content, .review-text, .review-body, [class*='review']")
        texts = [r.get_text(strip=True) for r in reviews if len(r.get_text(strip=True)) > 50]
        if texts:
            return "\n".join([f"- {t}" for t in texts[:20]]), "91mobiles"
    except Exception:
        pass
    return None, "Open site scrape failed"

# ─── Strategy 4: Flipkart HTML scrape ────────────────────────────────────────
def fetch_flipkart(url):
    try:
        resp = requests.get(url, headers=get_headers(), timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        # Flipkart review selectors (2024)
        for sel in ["div.ZmyHeo", "div.t-ZTKy", "div._6K-7Co", "div[class*='review']"]:
            blocks = soup.select(sel)
            if blocks:
                texts = [b.get_text(strip=True) for b in blocks[:20] if len(b.get_text(strip=True)) > 30]
                if texts:
                    return "\n".join([f"- {t}" for t in texts]), "Flipkart"
    except Exception:
        pass
    return None, "Flipkart scrape failed"

# ─── Master fetch logic ───────────────────────────────────────────────────────
def fetch_reviews(url):
    source = detect_source(url)
    log = []

    if source == "amazon":
        asin = extract_asin(url)
        if asin:
            reviews, msg = fetch_via_serpapi_amazon(asin)
            log.append(f"SerpAPI Amazon: {msg}")
            if reviews:
                return reviews, "Amazon (SerpAPI)", log
        # Fallback: Google search
        reviews, msg = fetch_via_google_search(url)
        log.append(f"Google Search: {msg}")
        if reviews:
            return reviews, "Google Snippets", log

    elif source == "flipkart":
        reviews, msg = fetch_flipkart(url)
        log.append(f"Flipkart HTML: {msg}")
        if reviews:
            return reviews, "Flipkart", log
        # Fallback: Google search
        reviews, msg = fetch_via_google_search(url)
        log.append(f"Google Search: {msg}")
        if reviews:
            return reviews, "Google Snippets", log

    else:
        # Generic: try direct scrape
        try:
            resp = requests.get(url, headers=get_headers(), timeout=12)
            soup = BeautifulSoup(resp.text, "lxml")
            for tag in soup(["script", "style", "nav", "header", "footer"]):
                tag.decompose()
            candidates = (soup.select("[class*='review']") or soup.select("[class*='comment']") or soup.select("blockquote"))
            texts = [c.get_text(strip=True) for c in candidates if len(c.get_text(strip=True)) > 40]
            if texts:
                return "\n".join([f"- {t}" for t in texts[:20]]), "Generic Page", log
        except Exception as e:
            log.append(f"Generic scrape failed: {e}")

        reviews, msg = fetch_via_google_search(url)
        log.append(f"Google Search: {msg}")
        if reviews:
            return reviews, "Google Snippets", log

    return None, source, log

# ─── AI Analysis ─────────────────────────────────────────────────────────────
def analyze_reviews(text, product_url=""):
    prompt = f"""You are a product research analyst. Analyze the following customer reviews and provide a detailed structured report.

Product URL: {product_url}

Customer Reviews:
{text}

Provide the following analysis in a clean, structured markdown format:

## 🏆 Top 5 Buying Reasons
List the top 5 reasons customers buy or love this product.

## ❌ Top 5 Complaints
List the top 5 issues customers face.

## 😊 Overall Sentiment
Positive / Neutral / Negative with explanation and estimated rating out of 5.

## 💡 Improvement Suggestions
4-5 actionable suggestions for the seller or manufacturer.

## 🎯 Target Customer Profile
Who is this product best suited for?

## 💰 Estimated Monthly Revenue Range
Based on review volume, price point, and category — rough estimate.
"""
    FREE_MODELS = [
        "openrouter/free",                              # Meta-router: auto-picks any working free model
        "google/gemma-3-27b-it:free",                  # Google Gemma 3 27B
        "meta-llama/llama-3.3-70b-instruct:free",      # Llama 3.3 70B
        "mistralai/mistral-small-3.1-24b-instruct:free", # Mistral Small 3.1
        "qwen/qwen3-8b:free",                          # Qwen 3 8B
        "meta-llama/llama-4-scout:free",               # Llama 4 Scout
        "meta-llama/llama-3.2-3b-instruct:free",       # Llama 3.2 3B (lightweight fallback)
    ]
    errors = []
    for model_id in FREE_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            err = str(e)
            errors.append(f"{model_id}: {err[:80]}")
            if "404" in err or "No endpoints" in err or "429" in err or "rate" in err.lower() or "unavailable" in err.lower():
                continue  # try next model
            return f"⚠️ **AI Error** ({model_id}): {err}"
    return f"⚠️ All free models are currently unavailable. Please try again in a moment.\n\n**Details:** {'; '.join(errors)}"

# ─── Competitor finder ────────────────────────────────────────────────────────
def get_competitors(query):
    if not SERPAPI_KEY or not query.strip():
        return []
    try:
        res = requests.get("https://serpapi.com/search.json", params={
            "engine": "amazon",
            "k": query,
            "api_key": SERPAPI_KEY
        }, timeout=10).json()
        products = res.get("organic_results", [])[:5]
        return [(p.get("title"), p.get("price"), p.get("rating")) for p in products]
    except Exception:
        return []

# ─── Streamlit UI ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Amazon Review Analytics", page_icon="🛒", layout="wide")
st.title("🛒 Amazon Review Analytics Tool")
st.caption("Paste any Amazon or Flipkart URL — or any website — and get AI-powered insights from real reviews.")

product_url = st.text_input("🔗 Enter Product URL", placeholder="https://www.amazon.in/dp/B0XXXXXXXX")
competitor_keyword = st.text_input("🔍 Competitor keyword (optional)", placeholder="e.g. wireless earbuds under 2000")

st.markdown("**Or paste reviews manually** if the URL scrape fails:")
manual_reviews = st.text_area("📋 Paste reviews here (one per line)", height=120, placeholder="Great product, battery lasts 2 days...\nMic quality is poor...\nBest in this price range...")

if st.button("🚀 Analyze", type="primary"):
    reviews = None
    source_label = "Manual"

    # Use manual input if provided
    if manual_reviews.strip():
        reviews = manual_reviews.strip()
        source_label = "Manual Input"
        st.success(f"✅ Using your manually pasted reviews ({len(reviews.splitlines())} lines).")

    elif product_url.strip():
        with st.spinner("🔍 Trying to scrape reviews..."):
            reviews, source_label, debug_log = fetch_reviews(product_url.strip())

        with st.expander("🛠 Scraping Debug Log", expanded=False):
            for entry in debug_log:
                st.text(entry)

        if not reviews:
            st.error(
                "❌ Could not auto-scrape reviews from this page.\n\n"
                "**Why this happens:** Amazon & Flipkart block automated requests heavily.\n\n"
                "**What you can do:**\n"
                "- Copy-paste reviews from the product page into the text box above\n"
                "- Make sure your **SerpAPI key** is set in `.env` (for Amazon)\n"
                "- Try a Flipkart URL — it works more reliably"
            )
        else:
            review_lines = [l for l in reviews.splitlines() if l.strip()]
            st.success(f"✅ Got **{len(review_lines)} review snippets** via {source_label}!")
            with st.expander("📝 Raw Reviews", expanded=False):
                st.text(reviews)
    else:
        st.warning("Please enter a product URL or paste reviews manually.")

    if reviews:
        with st.spinner("🤖 AI analyzing reviews..."):
            insights = analyze_reviews(reviews, product_url)

        st.markdown("---")
        st.subheader("📊 AI-Powered Insights")
        st.markdown(insights)

        if competitor_keyword.strip():
            st.markdown("---")
            st.subheader("🆚 Competitor Products")
            with st.spinner("Fetching competitors..."):
                competitors = get_competitors(competitor_keyword)
            if competitors:
                for title, price, rating in competitors:
                    st.write(f"- **{title}** | Price: {price or 'N/A'} | Rating: {rating or 'N/A'}")
            else:
                st.info("No competitors found. Check your SerpAPI key or try a different keyword.")