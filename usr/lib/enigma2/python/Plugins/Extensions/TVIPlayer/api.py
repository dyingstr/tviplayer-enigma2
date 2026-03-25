import re
import json
import ssl
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import logging
import os

# File logger — always writes to /tmp/tviplayer.log regardless of
# Enigma2's existing log configuration
log = logging.getLogger("tviplayer")
log.setLevel(logging.DEBUG)
if not log.handlers:
    _fh = logging.FileHandler("/tmp/tviplayer.log")
    _fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(_fh)
    log.propagate = False

# SSL context that skips certificate verification
# (needed on boxes with outdated CA bundles)
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

BASE_URL = "https://tviplayer.iol.pt"
MATRIX_URL = "https://services.iol.pt/matrix?userId="
LOGIN_URL = "https://services.iol.pt/sso/signin"
IMG_BASE = "https://img.iol.pt/image/id/{img_id}/220"

# Categories as they appear on the /programas page
CATEGORIES = ["Ficção", "Entretenimento", "Informação", "CNN", "Filmes"]

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)


def _js_to_json(js_str):
    """Convert a loose JavaScript object/array string to valid JSON."""
    # Remove single-line comments
    js_str = re.sub(r'//[^\n]*', '', js_str)
    # Remove multi-line comments
    js_str = re.sub(r'/\*.*?\*/', '', js_str, flags=re.DOTALL)
    # Quote unquoted keys:  key: → "key":
    js_str = re.sub(r'(?<=[{,\[]\s*)([A-Za-z_]\w*)\s*:', r'"\1":', js_str)
    js_str = re.sub(r',\s*}', '}', js_str)
    js_str = re.sub(r',\s*]', ']', js_str)
    return js_str


class TVIPlayerAPI:
    def __init__(self):
        self._token = None
        jar = http.cookiejar.CookieJar()
        https_handler = urllib.request.HTTPSHandler(context=_SSL_CTX)
        self._opener = urllib.request.build_opener(
            https_handler,
            urllib.request.HTTPCookieProcessor(jar),
        )

    def _get(self, url):
        log.debug("GET %s", url)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with self._opener.open(req, timeout=20) as resp:
            data = resp.read().decode("utf-8", errors="replace")
            log.debug("GET %s -> %d bytes", url, len(data))
            return data

    def _post(self, url, data):
        log.debug("POST %s", url)
        encoded = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(
            url, data=encoded,
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        with self._opener.open(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")

    # ------------------------------------------------------------------ #
    # Auth                                                                 #
    # ------------------------------------------------------------------ #

    def get_token(self):
        """Fetch a fresh wmsAuthSign token (anonymous, no credentials needed)."""
        self._token = self._get(MATRIX_URL).strip()
        log.debug("Token fetched: %s...", self._token[:30])
        return self._token

    def login(self, email, password):
        """Authenticate with IOL account (optional, for gated content)."""
        try:
            self._post(LOGIN_URL, {"email": email, "password": password})
            log.debug("Login OK for %s", email)
        except Exception as e:
            log.warning("Login failed (non-fatal): %s", e)

    # ------------------------------------------------------------------ #
    # Catalog                                                              #
    # ------------------------------------------------------------------ #

    def get_shows(self, category=None):
        """Scrape /programas and return shows, optionally filtered by category.

        The page structure is:
          <h2><span>Category Name</span></h2>
          ...
          <div class="item">
            <img src="https://img.iol.pt/image/id/{img_id}/220" alt="{title}">
            <div class="item--name">{title}</div>
            <a href="https://tviplayer.iol.pt/programa/{slug}/{show_id}">

        Returns list of dicts:
            {title, slug, show_id, thumb_url, category}
        """
        html = self._get(BASE_URL + "/programas")
        shows = []
        seen = set()

        # Split the page into sections by category heading
        # Pattern: <span>Category</span> marks the start of a category block
        cat_names = "|".join(re.escape(c) for c in CATEGORIES)
        section_split = re.split(
            r'<span>\s*(' + cat_names + r')\s*</span>',
            html,
            flags=re.IGNORECASE
        )

        # section_split layout: [pre, cat1, content1, cat2, content2, ...]
        current_cat = "Outro"
        chunks = []
        if len(section_split) > 1:
            for i in range(1, len(section_split), 2):
                raw_cat = section_split[i].strip()
                # Normalize to the canonical category name (case-insensitive match)
                cat = raw_cat
                for c in CATEGORIES:
                    if c.lower() == raw_cat.lower():
                        cat = c
                        break
                content = section_split[i + 1] if i + 1 < len(section_split) else ""
                chunks.append((cat, content))
        else:
            # Fallback: treat entire page as one section
            chunks = [("Outro", html)]

        for cat, content in chunks:
            # Split content into individual item blocks by <div class="item">
            # Each item contains: img, item--name div, and an <a href> link
            item_blocks = content.split('<div class="item">')
            for item_html in item_blocks[1:]:  # skip the pre-first-item content
                # Link: href="https://tviplayer.iol.pt/programa/{slug}/{id}"
                link_m = re.search(
                    r'href="https://tviplayer\.iol\.pt/programa/([\w-]+)/([a-f0-9]{24})"',
                    item_html
                )
                if not link_m:
                    continue
                slug = link_m.group(1)
                show_id = link_m.group(2)

                if show_id in seen:
                    continue
                seen.add(show_id)

                # Thumbnail: <img src="https://img.iol.pt/image/id/{id}/220" alt="{title}">
                img_m = re.search(
                    r'<img\s+src="(https://img\.iol\.pt/image/id/[^"]+)"[^>]*alt="([^"]*)"',
                    item_html
                )
                thumb_url = img_m.group(1) if img_m else ""
                alt_title = img_m.group(2) if img_m else ""

                # Title from item--name div
                name_m = re.search(r'<div class="item--name">([^<]+)</div>', item_html)
                title = name_m.group(1).strip() if name_m else alt_title.strip()

                if not title:
                    title = slug.replace("-", " ").title()

                shows.append({
                    "title": title,
                    "slug": slug,
                    "show_id": show_id,
                    "thumb_url": thumb_url,
                    "category": cat,
                })

        if category:
            shows = [s for s in shows if s["category"].lower() == category.lower()]

        return shows

    # ------------------------------------------------------------------ #
    # Episodes                                                             #
    # ------------------------------------------------------------------ #

    def get_episodes(self, slug, show_id):
        """Scrape the show page and return episodes.

        The page uses <li class="item"> blocks with:
          <span class="item--ep">EP 110</span>
          <span class="item--title">Title here</span>
          <span class="item--date">Ontem / Seg, 24 mar</span>
          <img src="https://img.iol.pt/image/id/{id}/340">
          <a href="/programa/{slug}/{id}/episodio/{ep_id}">

        Returns list of dicts:
            {title, ep_num, ep_id, ep_type, url, thumb_url, air_date}
        """
        html = self._get("{}/programa/{}/{}".format(BASE_URL, slug, show_id))
        episodes = []
        seen = set()

        for block in html.split('<li class="item"')[1:]:
            # Link (required — skip block if missing)
            link_m = re.search(
                r'href="(?:https?://tviplayer\.iol\.pt)?'
                r'/programa/([\w-]+)/([a-f0-9]{24})/(video|episodio)/([\w]+)"',
                block
            )
            if not link_m:
                continue
            ep_slug, ep_show_id, ep_type, ep_id = link_m.groups()
            key = (ep_show_id, ep_id)
            if key in seen:
                continue
            seen.add(key)

            url = "{}/programa/{}/{}/{}/{}".format(
                BASE_URL, ep_slug, ep_show_id, ep_type, ep_id
            )

            # Title from item--title span (most reliable source)
            title_m = re.search(r'<span class="item--title">([^<]+)</span>', block)
            if title_m:
                title = title_m.group(1).strip()
            else:
                # fallback: aria-label on the <a>
                aria_m = re.search(r'aria-label="([^"]{2,120})"', block)
                title = aria_m.group(1).strip() if aria_m else ep_id

            # Episode number
            ep_num_m = re.search(r'<span class="item--ep">\s*([^<]+)\s*</span>', block)
            ep_num = ep_num_m.group(1).strip() if ep_num_m else ""

            # Air date from item--date span (e.g. "Ontem", "Seg, 24 mar")
            date_m = re.search(
                r'<span class="item--date">[^<]*<span[^>]*>[^<]*</span>\s*([^<]+)',
                block
            )
            if not date_m:
                date_m = re.search(r'<span class="item--date">\s*([^<]+)\s*</span>', block)
            air_date = date_m.group(1).strip() if date_m else ""

            # Thumbnail
            img_m = re.search(r'<img\s+src="(https://img\.iol\.pt/image/id/[^"]+)"', block)
            thumb_url = img_m.group(1) if img_m else ""

            log.debug("Episode: %s | %s | %s | %s", ep_num, air_date, title[:40], ep_id)

            episodes.append({
                "title": title,
                "ep_num": ep_num,
                "ep_id": ep_id,
                "ep_type": ep_type,
                "url": url,
                "thumb_url": thumb_url,
                "air_date": air_date,
            })

        log.debug("get_episodes: found %d episodes for %s/%s", len(episodes), slug, show_id)
        return episodes

    # ------------------------------------------------------------------ #
    # Stream URL                                                           #
    # ------------------------------------------------------------------ #

    def get_stream_url(self, page_url):
        """Fetch a video page and return the authenticated HLS stream URL.

        Raises ValueError if stream URL cannot be found.
        """
        html = self._get(page_url)
        token = self.get_token()

        video_url = None

        # Try new pattern first (post May 2025): video: [{...}]
        m = re.search(r'(?<!-)\bvideo\s*:\s*(\[)', html)
        if m:
            try:
                bracket_start = m.start(1)
                depth = 0
                end = bracket_start
                for i in range(bracket_start, len(html)):
                    c = html[i]
                    if c == '[':
                        depth += 1
                    elif c == ']':
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
                raw = html[bracket_start:end]
                # Try plain JSON first (it usually is valid JSON)
                try:
                    arr = json.loads(raw)
                except json.JSONDecodeError:
                    arr = json.loads(_js_to_json(raw))
                if arr and isinstance(arr, list):
                    video_url = arr[0].get("videoUrl")
            except Exception:
                pass

        # Fallback: old pattern jsonData = {...}
        if not video_url:
            m = re.search(r'jsonData\s*=\s*(\{[^;]+\})', html, re.DOTALL)
            if m:
                try:
                    data = json.loads(_js_to_json(m.group(1)))
                    video_url = data.get("videoUrl")
                except Exception:
                    pass

        if not video_url:
            raise ValueError("Não foi possível encontrar o URL do vídeo na página.")

        return "{}?wmsAuthSign={}".format(video_url, urllib.parse.quote(token))
