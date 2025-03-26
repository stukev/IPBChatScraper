import argparse
import json
import time
import random
import requests
import browser_cookie3
from typing import Optional, List
from bs4 import BeautifulSoup
import re
import os

# === Constants ===
MARKER = "__full_backup_complete__"
DEFAULT_LAST_ID = '99999999999999'


def parse_args():
    parser = argparse.ArgumentParser(description="Archive messages from an IPB chatbox.")

    parser.add_argument('--url', required=True, help='Base URL of the IPB forum (e.g. https://example.com/index.php)')
    parser.add_argument('--room', default='1', help='Chatbox room ID (default: 1)')
    parser.add_argument('--output', default='chatlog.jsonl', help='Output file path (default: chatlog.jsonl)')

    parser.add_argument('--use-browser', action='store_true', help='Extract session cookie from browser')
    parser.add_argument('--browser', choices=['firefox', 'chrome'], help='Browser to extract cookies from (required with --use-browser)')

    parser.add_argument('--cookie', help='ips4_IPSSessionFront cookie value (manual mode only)')
    parser.add_argument('--csrf', help='CSRF key (manual mode only)')

    args = parser.parse_args()

    if args.use_browser and not args.browser:
        parser.error('--browser is required when using --use-browser')

    if not args.use_browser:
        if not args.cookie:
            parser.error('--cookie is required in manual mode')
        if not args.csrf:
            parser.error('--csrf is required in manual mode')

    return args


def extract_csrf_from_html(url: str, cookie_jar) -> str:
    try:
        response = requests.get(url, cookies=cookie_jar, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        meta_tag = soup.find('meta', attrs={'name': 'csrfKey'})
        if meta_tag and meta_tag.get('content'):
            return meta_tag['content']

        match = re.search(r'csrfKey\s*:\s*\"([a-f0-9]{32})\"', response.text)
        if match:
            return match.group(1)

        exit("Exiting: Could not find csrfKey in page HTML.")

    except Exception as e:
        exit(f"Exiting: Failed to extract csrfKey from HTML. Error: {e}")


def get_cookie_jar(browser: str, domain: str):
    if browser == 'firefox':
        return browser_cookie3.firefox(domain_name=domain)
    elif browser == 'chrome':
        return browser_cookie3.chrome(domain_name=domain)
    else:
        exit("Unsupported browser for cookie extraction.")


def extract_session_cookie(cookie_jar) -> str:
    for cookie in cookie_jar:
        if cookie.name == 'ips4_IPSSessionFront':
            return cookie.value
    exit('Exiting: Could not find ips4_IPSSessionFront in browser cookies.')


def validate_credentials(session_cookie: str, csrf_token: str) -> None:
    if len(session_cookie) != 26:
        exit(f'Exiting: Session cookie should be 26 characters. Got {len(session_cookie)}.')
    if len(csrf_token) != 32:
        exit(f'Exiting: CSRF token should be 32 characters. Got {len(csrf_token)}.')


def build_request(session_cookie: str, csrf_token: str, last_id: str, room_id: str, use_cookie_header=True):
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }
    if use_cookie_header:
        headers['Cookie'] = f'ips4_IPSSessionFront={session_cookie};'

    params = {
        'app': 'chatbox',
        'module': 'chatbox',
        'controller': 'room',
        'id': room_id,
        'joined': room_id,
        'do': 'getMSG'
    }

    data = {
        'csrfKey': csrf_token,
        'lastID': last_id,
        'firstLoad': '0',
        'loadMoreMode': '1',  # Crawl backward in time
        'isReconnect': '0'
    }

    return headers, params, data


def fetch_messages(url: str, headers: dict, params: dict, data: dict, retries: int = 3, cookie_jar=None) -> Optional[dict]:
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, params=params, data=data, cookies=cookie_jar)
            print(f"[DEBUG] HTTP {response.status_code}")
            print(f"[DEBUG] Response text: {response.text[:500]}")  # Print first 500 chars
            if response.text:
                if response.text == '{"cacheLevel":"0","content":"","lastID":"","noOlder":"1"}':
                    return {"noOlder": True, "content": []}
                check_for_errors(response.text, data['lastID'])
                return json.loads(response.text)
        except requests.RequestException as e:
            print(f"[ERROR] Request failed on attempt {attempt+1}: {e}")
        time.sleep(2)
    exit("Exiting: Failed after 3 retries. Server may be down or blocking requests.")


def check_for_errors(response_text: str, last_id: str) -> None:
    if response_text == 'Something went wrong. Please try again.':
        exit('Exiting: CSRF token is invalid or expired.')
    if response_text.startswith('{"redirect"'):
        exit('Exiting: Session cookie is invalid or expired.')


def strip_metadata(message: dict) -> dict:
    keys_to_remove = ['chatterKey', 'sys', 'inDay', 'donation', 'canEdit', 'canDelete', 'canReport']
    return {k: v for k, v in message.items() if k not in keys_to_remove}


def load_existing_ids(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    ids = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip() == MARKER:
                break
            try:
                data = json.loads(line)
                ids.append(data['id'])
            except:
                continue
    return ids


def prepend_to_file(path: str, lines: List[str]):
    # Prepend new messages to the beginning of the file
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
            f.write(MARKER + '\n')
        return

    with open(path, 'r', encoding='utf-8') as f:
        old = f.readlines()

    with open(path, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\n')
        f.writelines(old)


def main():
    args = parse_args()

    # Get credentials (cookie + csrf)
    if args.use_browser:
        domain = args.url.split('//')[-1].split('/')[0]
        cookie_jar = get_cookie_jar(args.browser, domain)
        session_cookie = extract_session_cookie(cookie_jar)
        csrf_token = extract_csrf_from_html(args.url, cookie_jar)
    else:
        cookie_jar = None
        session_cookie = args.cookie
        csrf_token = args.csrf

    validate_credentials(session_cookie, csrf_token)

    print("Starting shoutbox sync...")

    # Load previously backed-up IDs (if any)
    existing_ids = load_existing_ids(args.output)
    newest_stored = existing_ids[0] if existing_ids else None

    last_id = DEFAULT_LAST_ID  # Always start from latest known ID
    done = False

    with open(args.output, 'a', encoding='utf-8') as outfile:
        while not done:
            headers, params, data = build_request(session_cookie, csrf_token, last_id, args.room, use_cookie_header=not args.use_browser)
            response = fetch_messages(args.url, headers, params, data, cookie_jar=cookie_jar if args.use_browser else None)

            if response.get('noOlder'):
                print("Reached beginning of shoutbox history.")
                done = True
                break

            messages = response.get('content', [])
            if not messages:
                print("No more messages found. Archive is up to date.")
                done = True
                break

            for msg in messages:
                msg_id = msg['id']
                if msg_id in existing_ids:
                    print(f"Stopped at known message ID {msg_id} (already backed up).")
                    done = True
                    break

                cleaned = strip_metadata(msg)
                line = json.dumps(cleaned, ensure_ascii=False)
                outfile.write(line + '\n')
                last_id = msg_id  # Move pointer backward

            time.sleep(random.uniform(3, 5))

    print("Sync complete. Exiting.")


if __name__ == "__main__":
    main()
