
#!/usr/bin/env python3
"""
sku_lookup_worker.py
Searches firesecurityproducts.com for each SKU and logs product title and mapped technology.
Preferentially uses the site's search, falls back to SerpAPI if available, otherwise uses polite DuckDuckGo HTML search.
Outputs sku_lookup_log.csv with columns: sku, found_url, product_title, mapped_technology, confidence, notes
""" 
import os, time, csv, re, json
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).parent
ORDERS = BASE / "clean_orders.csv"
LOG = BASE / "sku_lookup_log.csv"
TOTALS = BASE / "totals.json"
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")

def read_unique_skus(limit=None):
    import pandas as pd
    if not ORDERS.exists():
        return []
    df = pd.read_csv(ORDERS, dtype=str)
    if 'sku' not in df.columns:
        return []
    counts = df['sku'].value_counts().to_dict()
    skus = sorted(counts.keys(), key=lambda k: -counts[k])
    if limit:
        skus = skus[:limit]
    return skus

def site_search_firesecurity(sku):
    # Try site's search endpoint (query param 's' common on WP sites)
    try:
        q = sku.strip()
        url = f"https://firesecurityproducts.com/?s={requests.utils.quote(q)}"
        r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # look for first product link in results
            a = soup.find("a", href=True, text=re.compile(re.escape(sku), re.I))
            if not a:
                # fallback: first result link
                a = soup.select_one("article a[href]") or soup.select_one(".result a[href]") or soup.find("a", href=True)
            if a and a['href']:
                target = a['href']
                # fetch target page title
                r2 = requests.get(target, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
                soup2 = BeautifulSoup(r2.text, "html.parser")
                title = soup2.title.string.strip() if soup2.title else ""
                return target, title, "site_search", "high"
    except Exception as e:
        return None, None, "error", "none"
    return None, None, "no_result", "none"

def serpapi_search(sku):
    if not SERPAPI_KEY:
        return None, None, "no_key", "none"
    try:
        params = {"engine":"google", "q": f"site:firesecurityproducts.com {sku}", "api_key": SERPAPI_KEY}
        resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
        data = resp.json()
        if 'organic_results' in data and data['organic_results']:
            r0 = data['organic_results'][0]
            return r0.get('link'), r0.get('title'), "serpapi", "high"
    except Exception as e:
        return None, None, "error", "none"
    return None, None, "no_result", "none"

def duckduckgo_search(sku):
    try:
        q = f"site:firesecurityproducts.com {sku}"
        r = requests.get("https://html.duckduckgo.com/html?q=" + requests.utils.quote(q), timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            a = soup.find("a", href=True)
            if a and a['href']:
                url = a['href']
                r2 = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
                soup2 = BeautifulSoup(r2.text, "html.parser")
                title = soup2.title.string.strip() if soup2.title else ""
                return url, title, "duckduckgo", "medium"
    except Exception as e:
        return None, None, "error", "none"
    return None, None, "no_result", "none"

def map_title_to_tech(title):
    if not title: return "Other specialty detection"
    t = title.lower()
    if any(k in t for k in ["address", "addressable", "panel", "module", "zone", "control panel", "io module"]):
        return "Addressable system"
    if any(k in t for k in ["conventional", "bell", "sounder", "zone plate", "analog"]):
        return "Conventional system"
    if any(k in t for k in ["vesda","aspirating","aspiration","vedas","asp"]):
        return "Aspirating smoke detection"
    if any(k in t for k in ["wireless","zigbee","zwave","rf module","radio"]):
        return "Wireless detection system"
    if any(k in t for k in ["software","license","tool","configurator","app","firmware"]):
        return "Software & tools"
    if any(k in t for k in ["linear","lhd","linear heat","heat cable"]):
        return "Linear heat detection"
    if any(k in t for k in ["flame","uv flame","flame detector"]):
        return "Flame detection"
    if any(k in t for k in ["access","credential","reader","controller","door","strike"]):
        return "Security solutions"
    return "Other specialty detection"

def write_log(rows):
    with open(LOG, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sku","found_url","product_title","mapped_technology","confidence","notes"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

def main(batch_limit=500, pause_sec=1.2):
    skus = read_unique_skus(limit=batch_limit)
    rows = []
    for sku in skus:
        found = None
        # 1) site search
        url, title, note, conf = site_search_firesecurity(sku)
        if not url and SERPAPI_KEY:
            url, title, note, conf = serpapi_search(sku)
        if not url:
            url, title, note, conf = duckduckgo_search(sku)
        tech = map_title_to_tech(title or "")
        rows.append({"sku": sku, "found_url": url or "", "product_title": title or "", "mapped_technology": tech, "confidence": conf, "notes": note})
        time.sleep(pause_sec)
    write_log(rows)
    print(f"Wrote {LOG} with {len(rows)} entries")

if __name__ == "__main__":
    main(batch_limit=500)
