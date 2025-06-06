
import requests
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import csv
import sys
import time
import argparse
import json
import random
import logging
from bs4 import BeautifulSoup
from collections import deque

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
]

DEFAULT_TIMEOUT = 5
DEFAULT_CREDENTIALS = [
    ("admin", "admin"),
    ("admin", "password"),
    ("root", "root"),
    ("user", "user"),
    ("test", "test")
]

LOG_FILE = "scan_log.txt"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_wordlist(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"[!] Wordlist load error: {e}")
        sys.exit(1)

def random_user_agent():
    return random.choice(DEFAULT_USER_AGENTS)

def identify_cms(html):
    signatures = {
        "wp-content": "WordPress",
        "Joomla!": "Joomla",
        "Drupal.settings": "Drupal",
        "Magento": "Magento",
        "prestashop": "PrestaShop",
        "static/shopify.js": "Shopify",
        "data-drupal-selector": "Drupal",
    }
    for key, cms in signatures.items():
        if key.lower() in html.lower():
            return cms
    return None

def is_login_page(html, path):
    login_keywords = ["login", "signin", "admin", "auth", "password"]
    if any(k in path.lower() for k in login_keywords):
        return True
    if any(k in html.lower() for k in ["password", "login"]):
        return True
    return False

def try_default_credentials(url, verbose=False):
    session = requests.Session()
    results = []

    try:
        r = session.get(url, timeout=DEFAULT_TIMEOUT)
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find("form")
        if form:
            inputs = form.find_all("input")
            user_field = None
            pass_field = None
            for inp in inputs:
                name = (inp.get("name") or "").lower()
                if not user_field and any(x in name for x in ["user", "login", "email"]):
                    user_field = inp.get("name")
                if not pass_field and any(x in name for x in ["pass", "password"]):
                    pass_field = inp.get("name")
            action = form.get("action")
            post_url = url if not action else urljoin(url, action)
            method = form.get("method", "post").lower()
            if user_field and pass_field:
                for user, pwd in DEFAULT_CREDENTIALS:
                    data = {user_field: user, pass_field: pwd}
                    try:
                        if verbose:
                            print(f"[*] Trying {user}:{pwd} at {post_url}")
                        if method == "post":
                            res = session.post(post_url, data=data, timeout=DEFAULT_TIMEOUT)
                        else:
                            res = session.get(post_url, params=data, timeout=DEFAULT_TIMEOUT)
                        if "logout" in res.text.lower() or "dashboard" in res.text.lower():
                            results.append(f"{user}:{pwd}")
                    except Exception as e:
                        logging.debug(f"Login attempt error for {user}:{pwd} at {post_url}: {e}")
            else:
                for user, pwd in DEFAULT_CREDENTIALS:
                    try:
                        if verbose:
                            print(f"[*] Trying basic auth {user}:{pwd} at {url}")
                        res = session.get(url, auth=(user, pwd), timeout=DEFAULT_TIMEOUT)
                        if res.status_code == 200 and not is_login_page(res.text, url):
                            results.append(f"{user}:{pwd}")
                    except Exception as e:
                        logging.debug(f"Basic auth error for {user}:{pwd} at {url}: {e}")
        else:
            for user, pwd in DEFAULT_CREDENTIALS:
                try:
                    if verbose:
                        print(f"[*] Trying basic auth {user}:{pwd} at {url}")
                    res = session.get(url, auth=(user, pwd), timeout=DEFAULT_TIMEOUT)
                    if res.status_code == 200 and not is_login_page(res.text, url):
                        results.append(f"{user}:{pwd}")
                except Exception as e:
                    logging.debug(f"Basic auth error for {user}:{pwd} at {url}: {e}")
    except Exception as e:
        logging.error(f"Error in try_default_credentials for {url}: {e}")
        return None
    return results if results else None

def find_hidden_forms(html):
    soup = BeautifulSoup(html, "html.parser")
    forms = []
    for form in soup.find_all("form"):
        hidden_inputs = form.find_all("input", type="hidden")
        if hidden_inputs:
            forms.append({
                "action": form.get("action"),
                "method": form.get("method", "get").lower(),
                "hidden_inputs": {inp.get("name"): inp.get("value", "") for inp in hidden_inputs}
            })
    return forms

def print_result(res):
    line = f"[+] [{res['status_code']}] {res['url']}"
    if res.get("cms"):
        line += f" | CMS: {res['cms']}"
    if res.get("login"):
        line += " | LOGIN"
    if res.get("credentials"):
        line += f" | DEFAULT CREDS: {','.join(res['credentials'])}"
    if res.get("hidden_forms"):
        line += f" | Hidden forms: {len(res['hidden_forms'])}"
    print(line)

def is_probably_directory(response, url):
    if url.endswith("/"):
        return True
    ct = response.headers.get("Content-Type", "")
    if "text/html" in ct.lower() and response.status_code in [200, 301, 302]:
        path = urlparse(url).path
        if "." not in path.split("/")[-1]:
            return True
    return False

def scan_path(base_url, path, proxies=None, verbose=False):
    session = requests.Session()
    headers = {"User-Agent": random_user_agent()}
    url = urljoin(base_url, path)
    if verbose:
        print(f"[*] Scanning: {url}")
    try:
        r = session.get(url, headers=headers, timeout=DEFAULT_TIMEOUT, proxies=proxies, allow_redirects=True)
        cms = identify_cms(r.text)
        login = is_login_page(r.text, path)
        creds = try_default_credentials(url, verbose) if login else None
        hidden_forms = find_hidden_forms(r.text) if login else []
        return {
            "url": url,
            "status_code": r.status_code,
            "cms": cms,
            "login": login,
            "credentials": creds,
            "hidden_forms": hidden_forms,
            "response": r,
        }
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return None

def threaded_scan(base_url, wordlist, max_depth, threads, proxies, delay, verbose=False):
    from collections import deque
    visited = set()
    results = []
    queue = deque()
    queue.append(("", 0))
    with ThreadPoolExecutor(max_workers=threads) as executor:
        while queue:
            batch = []
            while queue and len(batch) < threads:
                path, depth = queue.popleft()
                if path in visited or depth > max_depth:
                    continue
                visited.add(path)
                batch.append((path, depth))
            futures = {executor.submit(scan_path, base_url, path, proxies, verbose): (path, depth) for path, depth in batch}
            for future in as_completed(futures):
                try:
                    res = future.result()
                except Exception as e:
                    logging.error(f"Thread exception: {e}")
                    continue
                if res:
                    print_result(res)
                    results.append(res)
                    if is_probably_directory(res["response"], res["url"]):
                        next_depth = futures[future][1] + 1
                        if next_depth <= max_depth:
                            base_path = futures[future][0].rstrip("/")
                            for w in wordlist:
                                new_path = f"{base_path.rstrip('/')}/{w}" if base_path else w
                                if new_path not in visited:
                                    queue.append((new_path, next_depth))
            if delay > 0:
                time.sleep(delay + random.uniform(0, delay * 0.2))
    return results

def check_tor_connection(proxies):
    try:
        r = requests.get("https://check.torproject.org/api/ip", proxies=proxies, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("IsTor") == True:
                print("[✓] Tor proxy is working correctly.")
                return True
        print("[!] Tor proxy does not seem to be working.")
    except Exception as e:
        print(f"[!] Error checking Tor proxy: {e}")
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--wordlist", required=True)
    parser.add_argument("--threads", type=int, default=5)
    parser.add_argument("--max-depth", type=int, default=1)
    parser.add_argument("--proxy", default=None)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--use-tor", action="store_true", help="Use Tor SOCKS5 proxy at 127.0.0.1:9050")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    base_url = args.url
    if not base_url.startswith("http"):
        base_url = "http://" + base_url

    wordlist = load_wordlist(args.wordlist)

    proxies = None
    if args.use_tor:
        proxies = {
            "http": "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050"
        }
        print("[*] Using Tor proxy at 127.0.0.1:9050")
        if not check_tor_connection(proxies):
            print("[!] Please make sure Tor is running and configured correctly.")
            sys.exit(1)
    elif args.proxy:
        proxies = {"http": args.proxy, "https": args.proxy}
        print(f"[*] Using proxy {args.proxy}")

    print(f"[*] Starting scan on {base_url} with max-depth={args.max_depth} and threads={args.threads}")
    results = threaded_scan(base_url, wordlist, args.max_depth, args.threads, proxies, args.delay, verbose=args.verbose)

    valid_results = [r for r in results if r and r.get("status_code") in (200, 301, 302)]

    with open("found_paths.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Status Code", "CMS", "Login", "Default Creds", "Hidden Forms"])
        for r in valid_results:
            writer.writerow([
                r["url"], r["status_code"], r.get("cms") or "",
                r.get("login"), ",".join(r.get("credentials") or []),
                len(r.get("hidden_forms") or [])
            ])

    print(f"[✓] Scan finished. Results saved to found_paths.csv")

if __name__ == "__main__":
    main()
