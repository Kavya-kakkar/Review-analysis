# 🛒 Amazon Review Analytics Tool

> AI-powered product review scraper and sentiment analyzer — built with Streamlit, OpenRouter, and SerpAPI.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📌 What It Does

Paste any **Amazon** or **Flipkart** product URL and get instant AI-powered insights from real customer reviews:

| Insight | Description |
|---|---|
| 🏆 Top 5 Buying Reasons | Why customers love the product |
| ❌ Top 5 Complaints | Most common pain points |
| 😊 Overall Sentiment | Positive / Neutral / Negative + rating out of 5 |
| 💡 Improvement Suggestions | Actionable advice for sellers |
| 🎯 Target Customer Profile | Who this product is best suited for |
| 💰 Revenue Estimate | Rough monthly revenue range |
| 🆚 Competitor Products | Similar products from Amazon (via SerpAPI) |

---

## 🚀 Live Demo

> Deploy your own instance for free on [Streamlit Community Cloud](https://share.streamlit.io)

---

## 🧠 Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io)
- **AI Analysis**: [OpenRouter](https://openrouter.ai) (free LLMs — LLaMA 3.3, Gemma 3, Hermes 3)
- **Review Scraping**: BeautifulSoup + Requests
- **Search & Competitors**: [SerpAPI](https://serpapi.com) (Google + Amazon engines)

---

## ⚙️ Local Setup

### 1. Clone the repo

```bash
git clone https://github.com/Kavya-kakkar/Review-analysis.git
cd Review-analysis
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up API keys

Create a `.env` file in the root directory:

```env
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key
SERPAPI_KEY=your-serpapi-key
```

- 🔑 Get your **OpenRouter** key (free): [openrouter.ai/keys](https://openrouter.ai/keys)
- 🔑 Get your **SerpAPI** key (100 free searches/month): [serpapi.com](https://serpapi.com)

### 4. Run the app

```bash
python -m streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## ☁️ Deploy on Streamlit Cloud (Free)

1. Push this repo to GitHub (already done ✅)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New App**
3. Select this repo → branch `master` → file `app.py`
4. Click **Advanced settings** → add your secrets:

```toml
OPENROUTER_API_KEY = "sk-or-v1-your-key"
SERPAPI_KEY = "your-serpapi-key"
```

5. Hit **Deploy** 🎉
Live Link = https://review-analysis-jbb893jvwpnzaxmng4y7vt.streamlit.app/
---

## 🔄 How Scraping Works

The app uses a multi-strategy fallback pipeline to maximize review capture:

```
Amazon URL  →  SerpAPI Google Search  →  Direct HTML  →  Google Snippets
Flipkart URL  →  BeautifulSoup HTML  →  Google Snippets
Any URL  →  Generic selector scraping  →  Google Snippets
Manual paste  →  Always works ✅
```

> **Tip:** If auto-scraping fails (Amazon/Flipkart block bots), just copy-paste reviews manually into the text box provided in the UI.

---

## 🤖 AI Model Fallback Chain

OpenRouter free models are tried in order — if one is rate-limited or unavailable, the next is used automatically:

1. `meta-llama/llama-3.3-70b-instruct:free`
2. `google/gemma-3-27b-it:free`
3. `nousresearch/hermes-3-llama-3.1-405b:free`
4. `meta-llama/llama-3.2-3b-instruct:free`

---

## 📁 Project Structure

```
pixi ai/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── .gitignore          # Keeps secrets out of Git
├── .streamlit/
│   └── secrets.toml    # Local secrets (not committed)
└── README.md
```

---

## 🛡️ Security

- `.env` and `.streamlit/secrets.toml` are excluded from Git via `.gitignore`
- API keys on Streamlit Cloud are stored as encrypted secrets — never exposed in code

---

## 📄 License

MIT © [Kavya Kakkar](https://github.com/Kavya-kakkar)
