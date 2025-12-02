
# KGS Lead Estimator — Final Package

This repository contains the Streamlit lead estimator app and a SKU lookup worker to map SKUs to product pages on firesecurityproducts.com.

## What to upload to GitHub
Upload all files from this package to your `kgs-lead-estimator` repository root (keep `.github/workflows/sku_lookup.yml` in the correct path).

## Workflow
1. Push files to GitHub.
2. (Optional) Add `SERPAPI_KEY` repository secret for higher-quality search results.
3. Go to Actions → SKU Lookup Worker → Run workflow (set batch_limit if desired).
4. The workflow will produce `sku_lookup_log.csv` as an artifact. Download and review it.
5. Once mappings are validated, re-run any processing script to update `clean_orders.csv` and `totals.json` (or ask me to regenerate the final cleaned package for upload).

