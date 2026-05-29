# UCSB I&E data — dictionary

Public data, refreshed monthly. Sources: UCOP technology-transfer portal
(technologies) and the TIA Startup Database (ventures). Questions: info@innovation.ucsb.edu.

## Files
- `ucsb-ie.json` — everything (technologies + ventures + meta) in one file.
- `technologies.json` / `ventures.json` — split, used by the API.
- `ucsb-technologies.csv` / `ucsb-ventures.csv` — spreadsheet form (best for uploading
  into a Gemini Gem or a Custom GPT as knowledge).

## Technologies (available for licensing)
| field | meaning |
|---|---|
| `tech_id` | Stable portal ID. **Higher = more recently listed** on the marketplace. |
| `title` | Technology title. |
| `summary` | One-line plain-language summary (≤120 chars). |
| `disclosed_year` | Year the invention was disclosed to UC = the IP's **age**. From `uc_case`. |
| `uc_case` | UCSB docket number `YYYY-NNN-N` (YYYY = disclosure year). |
| `fields` | Top-level categories (the 18 rollups). |
| `categories` | All category tags (fields + sub-tags). |
| `inventors` | Inventor names (`Last, First`). |
| `patent_status` / `patents` | Patent text / structured patent rows (country, type, number, dated, case). |
| `description`, `advantages` | Longer prose from the portal. |
| `url` | The technology's public portal page. |

**Age vs. recency:** use `disclosed_year` for "how old is the IP / newest disclosures";
use `tech_id` (descending) for "most recently listed on the marketplace." They correlate
but are not identical.

## Ventures (UCSB startups)
| field | meaning |
|---|---|
| `company` | Company name. |
| `status` | Active / Acquired / Inactive. |
| `founded` | Founding year. |
| `industry` | Sector. |
| `licenses_ucsb_ip` | **true** = a "UCSB Startup" formed on a license/option to UCSB IP; **false** = a "UCSB Affiliated Startup" (UCSB-founded, no UCSB IP license). |
| `capital_raised` / `capital_raised_musd` | Disclosed capital (string / millions USD). |
| `founders` | Founder names. |
| `website`, `about` | Company site and one-line description. |

## Caveats
- Category counts overlap (a technology can carry several), so they sum to more than the
  unique technology count.
- "Stage" is not a field; `capital_raised` + `founded` + `status` are the available proxies.
- All figures are as published on the public sources; for anything authoritative or current,
  contact info@innovation.ucsb.edu.
