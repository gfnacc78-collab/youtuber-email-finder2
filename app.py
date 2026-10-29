import io
import os
import re
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Creator Contact Finder", page_icon="🎥", layout="wide")

API_BASE = "https://www.googleapis.com/youtube/v3"

st.title("🎥 YouTuber Finder")
st.caption("Free starter app · Discover channels and organize authorized business contacts")

st.info(
    "This tool discovers channels using the official YouTube Data API and stores contacts you "
    "supply or are authorized to use. It does not scrape YouTube pages, reveal hidden emails, "
    "or infer email addresses."
)

api_key = st.text_input(
    "YouTube Data API key (optional for importing channel URLs)",
    value=os.getenv("YOUTUBE_API_KEY", ""),
    type="password",
    help="Create a key in Google Cloud Console and enable YouTube Data API v3."
)

def youtube_get(endpoint, params):
    if not api_key:
        raise ValueError("Add a YouTube Data API key in the sidebar/main form first.")
    params = {**params, "key": api_key}
    response = requests.get(f"{API_BASE}/{endpoint}", params=params, timeout=20)
    if response.status_code != 200:
        try:
            detail = response.json().get("error", {}).get("message", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(f"YouTube API error ({response.status_code}): {detail}")
    return response.json()

def extract_channel_id(text):
    text = text.strip()
    if re.fullmatch(r"UC[\w-]{20,}", text):
        return text
    # Channel IDs are supported directly. Handles/custom URLs are not resolved by this
    # small starter app; ask the user to paste the channel ID from a channel URL.
    match = re.search(r"/channel/(UC[\w-]+)", text)
    if match:
        return match.group(1)
    return None

def get_channel_details(ids):
    rows = []
    for start in range(0, len(ids), 50):
        chunk = ids[start:start+50]
        if not chunk:
            continue
        data = youtube_get(
            "channels",
            {"part": "snippet,statistics", "id": ",".join(chunk), "maxResults": 50}
        )
        for item in data.get("items", []):
            sn = item.get("snippet", {})
            stats = item.get("statistics", {})
            channel_id = item["id"]
            rows.append({
                "channel_name": sn.get("title", ""),
                "channel_id": channel_id,
                "channel_url": f"https://www.youtube.com/channel/{channel_id}",
                "description": sn.get("description", "")[:500],
                "published_at": sn.get("publishedAt", ""),
                "subscribers": int(stats["subscriberCount"]) if stats.get("subscriberCount") else None,
                "video_count": int(stats["videoCount"]) if stats.get("videoCount") else None,
                "views": int(stats["viewCount"]) if stats.get("viewCount") else None,
            })
    return rows

if "channels" not in st.session_state:
    st.session_state.channels = pd.DataFrame(columns=[
        "channel_name", "channel_id", "channel_url", "description", "published_at",
        "subscribers", "video_count", "views", "business_email", "contact_source",
        "permission_or_basis", "contact_status", "notes"
    ])

tab_search, tab_urls, tab_contacts, tab_export = st.tabs([
    "🔎 Keyword search", "🔗 Channel URLs / IDs", "✉️ Contacts", "📤 Export"
])

with tab_search:
    st.subheader("Discover channels by keyword")
    with st.form("search_form"):
        keyword = st.text_input("Niche or keyword", placeholder="e.g. Minecraft, home fitness, budget tech")
        region = st.selectbox("Region", ["Any region", "US", "CA", "GB", "AU", "IN"])
        language = st.selectbox("Language", ["Any language", "en", "fr", "es", "de", "pt"])
        result_count = st.slider("Maximum search results", 5, 50, 25, step=5)
        submitted = st.form_submit_button("Search channels", type="primary")
    if submitted:
        if not keyword.strip():
            st.warning("Enter a keyword.")
        else:
            try:
                params = {
                    "part": "snippet", "q": keyword.strip(), "type": "channel",
                    "maxResults": result_count, "order": "relevance"
                }
                if region != "Any region":
                    params["regionCode"] = region
                if language != "Any language":
                    params["relevanceLanguage"] = language
                with st.spinner("Searching YouTube's official API..."):
                    search_data = youtube_get("search", params)
                    ids = list(dict.fromkeys(
                        x.get("id", {}).get("channelId")
                        for x in search_data.get("items", [])
                        if x.get("id", {}).get("channelId")
                    ))
                    new_rows = get_channel_details(ids)
                old = st.session_state.channels
                new_df = pd.DataFrame(new_rows)
                if not new_df.empty:
                    for col in old.columns:
                        if col not in new_df.columns:
                            new_df[col] = ""
                    st.session_state.channels = pd.concat([old, new_df], ignore_index=True)
                    st.session_state.channels = st.session_state.channels.drop_duplicates(
                        subset=["channel_id"], keep="last"
                    ).reset_index(drop=True)
                    st.success(f"Added {len(new_df)} channel records. Review them in Contacts or Export.")
                else:
                    st.warning("No channels returned for that query.")
            except Exception as e:
                st.error(str(e))

with tab_urls:
    st.subheader("Import channel URLs or IDs")
    st.write("Paste one YouTube **channel ID** or `/channel/UC...` URL per line. Handles and custom URLs need their channel ID.")
    pasted = st.text_area("Channel IDs / URLs", height=160, placeholder="UCxxxxxxxxxxxxxxxxxxxxxx\nhttps://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxx")
    if st.button("Import channel details"):
        ids, invalid = [], []
        for line in pasted.splitlines():
            if not line.strip():
                continue
            channel_id = extract_channel_id(line)
            if channel_id:
                ids.append(channel_id)
            else:
                invalid.append(line.strip())
        ids = list(dict.fromkeys(ids))
        if not ids:
            st.warning("No supported channel IDs found.")
        else:
            try:
                with st.spinner("Loading channel details..."):
                    rows = get_channel_details(ids)
                old = st.session_state.channels
                new_df = pd.DataFrame(rows)
                if not new_df.empty:
                    for col in old.columns:
                        if col not in new_df.columns:
                            new_df[col] = ""
                    st.session_state.channels = pd.concat([old, new_df], ignore_index=True)
                    st.session_state.channels = st.session_state.channels.drop_duplicates(
                        subset=["channel_id"], keep="last"
                    ).reset_index(drop=True)
                    st.success(f"Imported {len(new_df)} channel(s).")
                if invalid:
                    st.warning("Could not recognize these as channel IDs/URLs: " + ", ".join(invalid[:10]))
            except Exception as e:
                st.error(str(e))

with tab_contacts:
    st.subheader("Manage business contacts")
    st.caption("Only enter contacts the creator has publicly offered for business use or that you are otherwise authorized to process.")
    df = st.session_state.channels.copy()
    if df.empty:
        st.write("Search for channels or import IDs first.")
    else:
        edited = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "business_email": st.column_config.TextColumn("Business email"),
                "contact_source": st.column_config.TextColumn("Contact source / URL"),
                "permission_or_basis": st.column_config.TextColumn("Permission / basis"),
                "contact_status": st.column_config.SelectboxColumn(
                    "Status", options=["Not checked", "Creator supplied", "Authorized", "Verified separately", "Do not contact"]
                ),
                "notes": st.column_config.TextColumn("Notes")
            },
            disabled=["channel_id", "channel_url", "channel_name", "subscribers", "video_count", "views",
                      "description", "published_at"],
            key="contact_editor"
        )
        if st.button("Save contact edits", type="primary"):
            st.session_state.channels = edited
            st.success("Saved for this session. Export CSV to keep a local copy.")

with tab_export:
    st.subheader("Filter and export")
    df = st.session_state.channels.copy()
    if df.empty:
        st.write("No channel records yet.")
    else:
        min_subs = st.number_input("Minimum subscribers", min_value=0, value=0, step=1000)
        max_subs = st.number_input("Maximum subscribers (0 = no maximum)", min_value=0, value=0, step=1000)
        name_filter = st.text_input("Filter channel name")
        filtered = df.copy()
        if "subscribers" in filtered:
            filtered = filtered[filtered["subscribers"].fillna(0) >= min_subs]
            if max_subs > 0:
                filtered = filtered[filtered["subscribers"].fillna(0) <= max_subs]
        if name_filter:
            filtered = filtered[filtered["channel_name"].fillna("").str.contains(name_filter, case=False, regex=False)]
        st.metric("Channels matching filters", len(filtered))
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        csv = filtered.to_csv(index=False).encode("utf-8-sig")
        st.download_button("Download CSV", data=csv, file_name="youtube_creator_contacts.csv", mime="text/csv")
        st.caption("CSV is stored wherever you choose to download it. App session data is not a permanent database.")

st.divider()
st.caption("Privacy note: keep API keys private, use contact data only for a legitimate purpose, honor opt-outs, and follow applicable privacy and anti-spam laws.")
