# FrontOffice360 Roster Builder

Paste a school's official roster URL → get a partially-filled Excel file back,
plus a ready-made prompt to finish it in Claude.ai. No AI calls in this app
itself, so it's free forever with no message limits.

## What it does automatically (no AI, $0 cost)
- First/Last Name, Position (mapped to your system's valid codes), Jersey #,
  Height, Weight, Hometown, High School, Status ("Active"), College, Entry
  Year (estimated from class year), Red Shirt flag.

## What it leaves for the Claude.ai follow-up step
- Fun Facts and Academic Interests (these need a human/AI judgment call
  reading each player's bio page).
- Any position label the site uses that doesn't match your system's format
  (flagged in the app with a warning).

## Current coverage
Built for schools on the **Sidearm Sports** platform (confirmed working
against Iowa State's structure; Sidearm is the most common platform across
FBS/FCS programs, including Temple). Other platforms (PrestoSports, WMT
Digital) aren't supported yet -- the app will show an error rather than
return wrong data if it can't find a Sidearm-style roster table.

## How to test it locally first (recommended before deploying)
1. Install Python 3.10+ if you don't have it.
2. In this folder, run:
   ```
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. Your browser will open the app at `http://localhost:8501`. Test it
   against a couple of real schools (try Iowa State first, then Temple)
   before showing anyone else.

## How to deploy it for free (so you can send your boss a link)
1. Create a free GitHub account if you don't have one, and push this
   folder as a new repository (must include all 6 files: `app.py`,
   `scraper.py`, `template_filler.py`, `prompt_builder.py`,
   `requirements.txt`, and the template `.xlsx` file).
2. Go to https://share.streamlit.io and sign in with GitHub (free).
3. Click "New app," point it at your repo, and set the main file to
   `app.py`.
4. Deploy. You'll get a public URL like
   `https://your-app-name.streamlit.app` -- that's the link to send
   your boss.

## Known limitations to be upfront about
- Only tested against Iowa State's actual page structure so far (via a
  synthetic HTML test matching what was fetched live) -- test it against
  a few more real schools before treating it as fully reliable.
- Entry Year is an *estimate* based on listed class year (Fr./So./Jr./Sr.,
  redshirt-adjusted), not scraped data -- it's a reasonable guess, not a
  guarantee, and should be spot-checked.
- Bio-page-only fields (majors, personal fun facts) require the Claude.ai
  follow-up step by design -- this keeps the app's own AI usage at zero.
