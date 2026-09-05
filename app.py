import streamlit as st
from datetime import datetime

from scraper import scrape_roster
from template_filler import fill_template
from prompt_builder import build_finish_prompt

st.set_page_config(page_title="FrontOffice360 Roster Builder", page_icon="🏈")

st.title("🏈 FrontOffice360 Roster Builder")
st.write(
    "Paste a school's **official** athletics roster page URL below. "
    "This pulls the deterministic fields (name, position, height/weight, "
    "hometown, high school, jersey number) directly and fills them into "
    "our template automatically -- no AI, no cost, no message limits."
)

with st.form("roster_form"):
    school_name = st.text_input("School name (as it should appear in the College column)", placeholder="Iowa State University")
    roster_url = st.text_input("Official roster page URL", placeholder="https://cyclones.com/sports/football/roster")
    current_year = st.number_input("Current calendar year (for Entry Year estimates)", value=datetime.now().year, step=1)
    submitted = st.form_submit_button("Build spreadsheet")

if submitted:
    if not school_name or not roster_url:
        st.error("Please fill in both the school name and the roster URL.")
        st.stop()

    with st.spinner("Reading the roster page..."):
        try:
            result = scrape_roster(roster_url, current_calendar_year=int(current_year))
        except Exception as e:
            st.error(
                "Couldn't read that page. Either the URL is wrong, the site "
                f"blocked the request, or this school doesn't use the Sidearm "
                f"platform this scraper is built for.\n\nError detail: {e}"
            )
            st.stop()

    players = result["players"]
    if not players:
        st.error(
            "No players were found on that page. This usually means the site "
            "doesn't use the roster layout this tool expects (Sidearm Sports). "
            "You may need to fall back to the manual Claude.ai workflow for this school."
        )
        st.stop()

    st.success(f"Found {len(players)} athletes using the '{result['source_view']}' view.")

    if result["unmapped_positions"]:
        st.warning(
            "Heads up: these position labels didn't match our system's valid "
            f"list and couldn't be auto-converted: {', '.join(result['unmapped_positions'])}. "
            "They're included in the follow-up prompt below so Claude can fix them."
        )

    with st.expander("Preview scraped data"):
        st.dataframe(players)

    excel_buf = fill_template(
        template_path="FrontOffice360_Athlete_Roster_Template.xlsx",
        players=players,
        college_name=school_name,
    )

    st.download_button(
        "⬇️ Download partial spreadsheet",
        data=excel_buf,
        file_name=f"FrontOffice360_{school_name.replace(' ', '_')}_Roster.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.subheader("Next step: finish Fun Facts + Academic Interests")
    st.write(
        "These two fields need a human/AI judgment call, so they're not "
        "auto-filled. Download the file above, then paste the prompt below "
        "into a Claude.ai chat (along with the downloaded file and your "
        "completed Temple example) to finish it."
    )
    finish_prompt = build_finish_prompt(school_name, roster_url, players, result["unmapped_positions"])
    st.text_area("Prompt to paste into Claude.ai", finish_prompt, height=250)

st.caption(
    "Note: this currently supports schools on the Sidearm Sports platform "
    "(the most common one, used by Iowa State, Temple, and most FBS/FCS programs). "
    "Other platforms (PrestoSports, WMT Digital) aren't supported yet."
)
