# YouTuber Finder — free starter

## What it does
- Searches YouTube channels by keyword using the official YouTube Data API.
- Imports channel IDs or `/channel/UC...` URLs.
- Lets you manually record creator-supplied/authorized business contacts.
- Filters and exports records to CSV.

It does not scrape YouTube pages, uncover hidden emails, infer email addresses, or send messages.

## 1. Get a YouTube API key
1. Open https://console.cloud.google.com/
2. Create a project (or choose an existing one).
3. Enable **YouTube Data API v3**.
4. Create an API key under APIs & Services → Credentials.
5. Restrict the key to YouTube Data API v3 where possible. Keep it private.

YouTube API quota limits apply. Check the current quota in Google Cloud Console.

## 2. Install and run
Install Python 3.11+ from https://www.python.org/downloads/

Open a terminal in this folder and run:

### Windows
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, open Command Prompt and use:
```bat
.venv\Scripts\activate.bat
pip install -r requirements.txt
streamlit run app.py
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser. Paste your API key into the app. You can also set an environment variable named `YOUTUBE_API_KEY`.

## 3. Use it
- Keyword search: search a niche such as “Minecraft”.
- Channel URLs/IDs: paste channel IDs or `youtube.com/channel/UC...` URLs.
- Contacts: record only business contact details the creator has offered for business use or that you are otherwise authorized to process. Include source and status.
- Export: filter and download CSV.

The basic importer accepts channel IDs and `/channel/UC...` URLs. It does not resolve `@handles` or custom URLs automatically.

## Policy and privacy
YouTube API data must be handled under Google's current YouTube API Services Terms and Developer Policies. In particular, do not use the API to harvest contact information without consent, and do not scrape YouTube/Google pages. Review:
- https://developers.google.com/youtube/terms/developer-policies
- https://developers.google.com/youtube/terms/developer-policies-guide
- https://developers.google.com/youtube/data/reference/rest/v3/search/list

Respect applicable privacy, marketing, and anti-spam rules. Honor opt-outs. Do not treat an email as verified unless you verified it through an appropriate authorized process.

## Limitations
- API search is quota-limited and may return relevant videos/channels unevenly.
- Subscriber counts can be hidden or rounded.
- Contacts are user-entered; no email-finding or email-verification provider is bundled.
- Records persist only in the current app session until exported.
- This is a local prototype, not a production multi-user service.
