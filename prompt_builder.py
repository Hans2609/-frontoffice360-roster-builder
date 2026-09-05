def build_finish_prompt(school_name: str, roster_url: str, players: list, unmapped_positions: list) -> str:
    names = ", ".join(f"{p['first_name']} {p['last_name']}".strip() for p in players)

    unmapped_note = ""
    if unmapped_positions:
        unmapped_note = (
            "\n\nAlso, the scraper found these position labels that didn't match our system's "
            f"valid list and could not auto-convert them: {', '.join(unmapped_positions)}. "
            "Please check the roster page and fill in the correct converted position for those "
            "specific players."
        )

    return f"""Attached is a partially-filled roster spreadsheet for {school_name} (from {roster_url}) \
and our example of a fully completed roster (Temple) so you can see our exact formatting for \
the remaining fields.

Everything except Fun Facts and Academic Interests has already been filled in from the official \
roster page. Please finish the spreadsheet:

- For each player, visit their bio page on the official roster site and fill in:
  - Academic Interests: their stated major, if listed. Leave blank if not listed.
  - Fun Facts: something from the personal section of their bio, OR a notable high school stat \
(e.g. highly ranked recruit, played another sport in high school).
- Do not use outside sources -- only the official university bio page for each player.
- Leave any field blank rather than guessing if it isn't listed.
- Social media handles: enter the username only, no "@" symbol.{unmapped_note}

Players on this roster: {names}

Return the completed file in the same format as the attached partial spreadsheet."""
