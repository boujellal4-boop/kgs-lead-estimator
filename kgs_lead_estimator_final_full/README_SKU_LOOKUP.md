
# SKU Lookup Worker README

This worker searches `firesecurityproducts.com` first for each SKU and falls back to SerpAPI or DuckDuckGo if needed.

- The script is idempotent and polite (includes pauses).
- Start with batch_limit=500 to map the most valuable SKUs first.
- Review `sku_lookup_log.csv` after each run.
- After review, mappings can be applied to `clean_orders.csv` and totals recomputed.
