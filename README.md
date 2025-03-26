# IPBChatScraper

Scraping tool to backup Invision Power Board (IPB) "Chatbox" messages. Useful for OSINT, full archive persistence, quick grep lookups, or safeguarding against admin purges.

Tested with [Chatbox+](https://invisioncommunity.com/files/file/7465-chatbox-free/). Likely works with [Chatbox FREE](https://invisioncommunity.com/files/file/7465-chatbox-free/) too.

---

## Features

- Automatically extracts cookies from your browser (Chrome or Firefox)
- Automatically retrieves CSRF token from the site
- Archives the entire chatbox in **newest-to-oldest** order
- Detects and skips already archived messages

---

## Usage

### Option 1: Use Your Browser Session (Recommended)

1. Make sure you're logged into the forum in Firefox or Chrome.
2. Run the scraper:

```bash
python ipbchatscraper.py \
  --url https://www.forum.com/index.php \
  --use-browser \
  --browser firefox \
  --room 1 \
  --output full_shoutbox_backup.jsonl
```

> 💡 For Chrome use: `--browser chrome`

This will:
- Grab your active session cookie from the browser
- Extract the CSRF key automatically
- Back up the full chatbox (or just the new messages, if you’ve already backed it up before)

---

### Option 2: Manual Mode (Advanced)

If you can't use browser mode, provide session + CSRF manually:

```bash
python ipbchatscraper.py \
  --url https://www.forum.com/index.php \
  --csrf your_csrf_token \
  --cookie your_ips4_IPSSessionFront_cookie \
  --room 1 \
  --output full_shoutbox_backup.jsonl
```

To find the CSRF and cookie:
- **CSRF token**: Use F12 → Inspect → Search page source for `csrfKey`
- **Session cookie**: Look for `ips4_IPSSessionFront` under your browser’s cookies for the domain

---

## Output Format

- All messages are stored as newline-delimited JSON (JSONL)
- File is sorted **newest first** to reflect the Chat
- Once the archive is complete, the final line is:
  ```
  "__full_backup_complete__"
  ```

---

## Optional Parameters

| Flag            | Description                                         |
|-----------------|-----------------------------------------------------|
| `--room`        | Chat room ID (default: 1)                           |
| `--output`      | Output filename (default: `chatlog.jsonl`)         |
| `--use-browser` | Enables cookie + CSRF auto-extraction from browser |
| `--browser`     | Which browser to pull cookies from (`firefox`/`chrome`) |

---

## Known Behavior

- Some forums intermittently return “invalid CSRF” errors — the script automatically retries these.
- Messages are written to file immediately to avoid data loss on interruption.
- If the forum has purged very old messages, your backup will reflect only what the server returns.

---

## Installation

### 1. Clone this repo and set up a virtual environment:

```bash
git clone https://github.com/stukev/IPBChatScraper.git
cd IPBChatScraper
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Run the script:

```bash
python ipbchatscraper.py --help
```

> ✅ Supported Python versions: **3.7 and up** (tested with 3.10+)