#!/usr/bin/env python3
"""
Find dataset entries in lacuna_fund_datasets_updated.xlsx that are not yet in the
gold-standard Google Sheet (data_catalog.xlsx). Output a CSV with the same columns as
the Google Sheet so rows can be copy-pasted into the sheet.

Gold standard = Google Sheet (built as docs/data_catalog.xlsx).
Matching: primary key is normalized dataset link; secondary check by title similarity.
"""

import csv
import re
import pandas as pd
from urllib.parse import urlparse, urlunparse

# Google Sheet column order (from backup CSV header row)
SHEET_HEADERS = [
    "Project ID",
    "Catchy Title [for dataset]",
    "Catchy Title [for use case, application]",
    "Country / Region ",
    "What this is about/Description",
    "Access to the dataset [link]",
    "Access to AI Model, Software, AI Application [link]",
    "Sector /Sustainable Development Goal ",
    "Maturity / Readiness for replication or scaling [INTERNAL]",
    "Type of Data",
    "Point of contact & community support ",
    "Data characteristics: how to use it & key characteristics ",
    "Model characteristics: How to use & key characteristics of the AI Model, Software, AI Application",
    "How to use it: How can you concretely work with this and built on this? How much will this cost and which resources are available to help me? ",
    "Organizations involved - including logos, links and visual elements",
    "Editor of this information:",
    "Technical Domain",
    "Expressive visualization / picture related to dataset / possible use / story-tellling",
    "License",
    "Additional Resources (Paper, Publications, etc)",
    "GIZ Funded (Yes/No)",
    "Info on fair sharing as as Digital Public Good ",
    "Comments",
]

URL_PATTERN = re.compile(r"https?://[^\s\]\)\;\,\"\']+", re.IGNORECASE)


def normalize_url(u: str) -> str | None:
    if not u or not str(u).strip():
        return None
    u = str(u).strip()
    if not u.startswith("http"):
        return None
    try:
        parsed = urlparse(u)
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/") or "/"
        # Use https for comparison so http and https match
        scheme = "https" if parsed.scheme in ("http", "https") else parsed.scheme
        clean = urlunparse((scheme, netloc, path, "", "", ""))
        return clean
    except Exception:
        return u


def _kaggle_canonical(url: str) -> str | None:
    """Reduce Kaggle dataset URL variants to same form for matching."""
    if not url or "kaggle.com" not in url:
        return None
    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        # .../datasets/username/name or .../username/name -> username/name
        if path.startswith("datasets/"):
            path = path[len("datasets/") :]
        return (parsed.netloc.lower(), path)
    except Exception:
        return None


def extract_urls(text: str) -> list[str]:
    if pd.isna(text):
        return []
    text = str(text)
    urls = URL_PATTERN.findall(text)
    return [normalize_url(u) for u in urls if normalize_url(u)]


def build_gold_links_and_titles(
    df: pd.DataFrame,
) -> tuple[set[str], set[tuple[str, str]], set[str], dict[str, str]]:
    links = set()
    kaggle_canonicals = set()
    titles = []
    title_to_project_id: dict[str, str] = {}
    for col in ["Dataset Link", "Model/Use-Case Links", "Access to the dataset [link]"]:
        if col not in df.columns:
            continue
        for v in df[col].dropna():
            for u in extract_urls(str(v)):
                if u:
                    links.add(u)
                    k = _kaggle_canonical(u)
                    if k:
                        kaggle_canonicals.add(k)
    for col in ["Dataset Speaking Titles", "Use Case Speaking Title", "Catchy Title [for dataset]", "Catchy Title [for use case, application]"]:
        if col in df.columns:
            for _, row in df.iterrows():
                t = row.get(col)
                if pd.notna(t) and str(t).strip():
                    key = str(t).strip().lower()
                    titles.append(key)
                    if "Project ID" in df.columns and key not in title_to_project_id:
                        title_to_project_id[key] = str(row["Project ID"]).strip()
    return links, kaggle_canonicals, set(titles), title_to_project_id


def is_in_gold_by_link(
    lacuna_urls: list[str],
    gold_links: set[str],
    gold_kaggle: set[tuple[str, str]],
) -> bool:
    for u in lacuna_urls:
        if not u:
            continue
        if u in gold_links:
            return True
        k = _kaggle_canonical(u)
        if k and k in gold_kaggle:
            return True
    return False


def safe_str(v, default=""):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return default
    return str(v).strip()


def main():
    gold_path = "docs/data_catalog.xlsx"
    lacuna_path = "lacuna/lacuna_fund_datasets_updated.xlsx"
    output_path = "lacuna/missing_candidates_for_google_sheet.csv"

    gold = pd.read_excel(gold_path)
    lacuna = pd.read_excel(lacuna_path)

    gold_links, gold_kaggle, gold_titles, title_to_project_id = build_gold_links_and_titles(gold)
    next_ui = 81
    if "Project ID" in gold.columns:
        nums = [int(m.group(1)) for s in gold["Project ID"].dropna().astype(str) for m in [re.search(r"ui_(\d+)", s)] if m]
        if nums:
            next_ui = max(nums) + 1

    missing_rows = []
    link_updates: list[dict[str, str]] = []
    for idx, row in lacuna.iterrows():
        link_cell = row.get("Link to Dataset", "")
        lacuna_urls = extract_urls(link_cell)
        if not lacuna_urls:
            continue
        if is_in_gold_by_link(lacuna_urls, gold_links, gold_kaggle):
            continue
        title = safe_str(row.get("Title", ""))
        title_lower = title.lower() if title else ""
        suggested_link = safe_str(link_cell).split(";")[0].strip() if link_cell else ""

        # Same project already in gold by title? -> suggest link update, do not add as new row
        if title_lower and title_lower in gold_titles:
            pid = title_to_project_id.get(title_lower, "")
            mask = pd.Series(False, index=gold.index)
            for col in ["Dataset Speaking Titles", "Use Case Speaking Title"]:
                if col in gold.columns:
                    mask |= gold[col].astype(str).str.strip().str.lower() == title_lower
            gold_row = gold[mask]
            current_link = ""
            if not gold_row.empty:
                current_link = safe_str(gold_row.iloc[0].get("Dataset Link", ""))
                if not pid and "Project ID" in gold_row.columns:
                    pid = safe_str(gold_row.iloc[0]["Project ID"])
            note = "Gold had empty link" if not current_link else "Gold had different URL"
            link_updates.append({"Project ID": pid, "Catchy Title": title[:80], "Suggested dataset link": suggested_link, "Note": note})
            continue

        if not title:
            title = f"Dataset {idx+1}"

        # Build one row in Google Sheet column order
        out = {h: "" for h in SHEET_HEADERS}
        out["Project ID"] = f"ui_{next_ui}"
        next_ui += 1
        out["Catchy Title [for dataset]"] = title
        out["Catchy Title [for use case, application]"] = title
        out["Country / Region "] = safe_str(row.get("Country / Region", ""))
        out["What this is about/Description"] = safe_str(row.get("Description", ""))
        out["Access to the dataset [link]"] = suggested_link
        out["Sector /Sustainable Development Goal "] = safe_str(row.get("Domain", ""))
        out["Technical Domain"] = safe_str(row.get("Domain", ""))
        out["Point of contact & community support "] = safe_str(row.get("Point of Contact", ""))
        out["Editor of this information:"] = safe_str(row.get("Authors & Affiliations", ""))
        out["GIZ Funded (Yes/No)"] = "Yes"
        out["Info on fair sharing as as Digital Public Good "] = "This is a global digital public good under open-source licenses as named under \"licenses\" - Please consider fair sharing and giving back to communities in an appropriate way."
        missing_rows.append(out)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SHEET_HEADERS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(missing_rows)

    updates_path = "lacuna/link_update_suggestions.csv"
    with open(updates_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Project ID", "Catchy Title", "Suggested dataset link", "Note"], quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(link_updates)

    print(f"Gold standard: {len(gold)} rows, {len(gold_links)} unique dataset/model URLs.")
    print(f"Lacuna file: {len(lacuna)} rows.")
    print(f"Missing candidates (new rows to add): {len(missing_rows)}")
    print(f"Link-update suggestions (existing rows; do not add as new): {len(link_updates)}")
    print(f"Output: {output_path}")
    for r in missing_rows:
        print(f"  - {r['Project ID']}: {r['Catchy Title [for dataset]'][:60]}")
    if link_updates:
        print(f"Link updates: {updates_path}")
        for u in link_updates:
            print(f"  - {u['Project ID']}: {u['Catchy Title'][:50]} | {u['Note']}")


if __name__ == "__main__":
    main()
