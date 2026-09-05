"""
scraper.py
Scrapes an official college athletics roster page (Sidearm Sports platform)
and returns a clean list of player dicts. Sidearm is the most common
platform for D1 athletics sites (confirmed pattern on Iowa State's
cyclones.com, and used across most FBS/FCS programs).

Design notes:
- Sidearm roster pages typically render the roster in TWO redundant forms:
    1. "Card view" - one <li class="sidearm-roster-player"> per athlete,
       with sub-elements for name/position/height/etc.
    2. "Table view" (Alphabetical/Numeric roster) - a plain <table> with
       columns: #, Name, Pos., Ht., Wt., Yr., Hometown / High School.
  The table view is far easier and more reliable to parse (no nested
  card markup, no reliance on exact class names that can vary slightly
  site to site), so this scraper tries the table first and falls back
  to the card view if no table is found.
- This scraper is deliberately conservative: if a field can't be found,
  it returns None/blank rather than guessing, matching the "leave blank
  if not listed" rule established in the FrontOffice360 workflow.
- Only athletes are returned -- coaching/support staff tables are
  explicitly skipped by looking for the roster table's specific header
  row ("#", "Name", "Pos.", ...) rather than any generic table on the page.
"""

import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def _parse_height(raw: str):
    """'6' 4\"\"' or "6' 4''" -> "6'04''" (matches FrontOffice360 template format)."""
    if not raw:
        return None
    m = re.search(r"(\d+)'\s*(\d+)", raw)
    if not m:
        return None
    feet, inches = int(m.group(1)), int(m.group(2))
    return f"{feet}'{inches:02d}''"


def _parse_weight(raw: str):
    if not raw:
        return None
    m = re.search(r"(\d+)", raw)
    return int(m.group(1)) if m else None


POSITION_MAP = {
    "PK": "K",
    "PK/P": "K",
    "P/PK": "K",
    "ATH": None,   # no direct equivalent on the valid list; leave blank
    "EDGE": "DE",
    "OLB": "OLB",  # already valid
    "DB": "S",     # generic defensive back -> closest single valid code
}

VALID_POSITIONS = {
    "C", "CB", "DE", "DL", "DT", "FS", "ILB", "K", "KR", "LB", "LG", "LS",
    "LT", "MLB", "NT", "OG", "OL", "OLB", "OT", "P", "PR", "QB", "RB",
    "RG", "RT", "S", "SS", "TE", "WR",
}


def map_position(raw: str):
    if not raw:
        return None
    raw = raw.strip().upper()
    if raw in VALID_POSITIONS:
        return raw
    if raw in POSITION_MAP:
        return POSITION_MAP[raw]
    # unknown label: return as-is but flag it so the UI can warn the user
    return raw


def _split_hometown_highschool(raw: str):
    """'City, ST / High School' -> ('City, ST', 'High School')."""
    if not raw:
        return None, None
    if "/" in raw:
        parts = raw.split("/")
        hometown = parts[0].strip()
        highschool = "/".join(parts[1:]).strip() or None
        return hometown or None, highschool
    return raw.strip(), None


def _entry_year_from_class(class_year: str, current_calendar_year: int):
    """
    Best-effort estimate of the year the player entered college, derived
    from their listed academic class (e.g. 'R-Jr.', 'So.', 'Fr.').
    This is an ASSUMPTION, not scraped data -- surfaced separately in the
    output so it can be reviewed/corrected, matching the 'don't guess and
    present it as fact' principle used throughout this workflow.
    """
    if not class_year:
        return None
    cy = class_year.strip().lower()
    redshirt = cy.startswith("r-")
    cy = cy.replace("r-", "")
    year_map = {"fr.": 0, "so.": 1, "jr.": 2, "sr.": 3}
    offset = year_map.get(cy)
    if offset is None:
        return None
    if redshirt:
        offset += 1
    return current_calendar_year - offset


def parse_table_view(soup: BeautifulSoup):
    """Look for the plain table: # | Name | Pos. | Ht. | Wt. | Yr. | Hometown / High School"""
    for table in soup.find_all("table"):
        header_cells = [th.get_text(strip=True) for th in table.find_all("th")]
        header_text = " ".join(header_cells).lower()
        if "pos" in header_text and ("hometown" in header_text or "high school" in header_text):
            players = []
            for row in table.find_all("tr"):
                cells = [td.get_text(" ", strip=True) for td in row.find_all("td")]
                if len(cells) < 6:
                    continue
                jersey, name, pos, ht, wt, yr = cells[0], cells[1], cells[2], cells[3], cells[4], cells[5]
                hometown_hs = cells[6] if len(cells) > 6 else ""
                hometown, highschool = _split_hometown_highschool(hometown_hs)
                players.append({
                    "jersey": jersey.strip() or None,
                    "name": name.strip(),
                    "position_raw": pos.strip(),
                    "height_raw": ht.strip(),
                    "weight_raw": wt.strip(),
                    "class_year": yr.strip(),
                    "hometown": hometown,
                    "high_school": highschool,
                })
            if players:
                return players
    return []


def parse_card_view(soup: BeautifulSoup):
    """Fallback: Sidearm's <li class='sidearm-roster-player'> card markup."""
    players = []
    cards = soup.select("li.sidearm-roster-player")
    for card in cards:
        def text_of(selector):
            el = card.select_one(selector)
            return el.get_text(" ", strip=True) if el else None

        name = text_of(".sidearm-roster-player-name")
        jersey = text_of(".sidearm-roster-player-jersey-number")
        pos = text_of(".sidearm-roster-player-position")
        ht = text_of(".sidearm-roster-player-height")
        wt = text_of(".sidearm-roster-player-weight")
        yr = text_of(".sidearm-roster-player-academic-year")
        hometown = text_of(".sidearm-roster-player-hometown")
        highschool = text_of(".sidearm-roster-player-highschool")

        if not name:
            continue
        players.append({
            "jersey": jersey,
            "name": name,
            "position_raw": pos,
            "height_raw": ht,
            "weight_raw": wt,
            "class_year": yr,
            "hometown": hometown,
            "high_school": highschool,
        })
    return players


def scrape_roster(url: str, current_calendar_year: int = 2026):
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    raw_players = parse_table_view(soup)
    source_view = "table"
    if not raw_players:
        raw_players = parse_card_view(soup)
        source_view = "card"

    results = []
    unmapped_positions = set()
    for p in raw_players:
        first, last = "", ""
        name_parts = p["name"].split(" ")
        if name_parts:
            first = name_parts[0]
            last = " ".join(name_parts[1:])

        mapped_pos = map_position(p.get("position_raw"))
        if mapped_pos and mapped_pos not in VALID_POSITIONS:
            unmapped_positions.add(p.get("position_raw"))

        results.append({
            "first_name": first,
            "last_name": last,
            "position": mapped_pos,
            "position_raw": p.get("position_raw"),
            "jersey_number": p.get("jersey"),
            "height": _parse_height(p.get("height_raw")),
            "weight": _parse_weight(p.get("weight_raw")),
            "class_year": p.get("class_year"),
            "entry_year_estimate": _entry_year_from_class(p.get("class_year"), current_calendar_year),
            "hometown": p.get("hometown"),
            "high_school": p.get("high_school"),
        })

    return {
        "players": results,
        "source_view": source_view,
        "unmapped_positions": sorted(unmapped_positions),
    }
