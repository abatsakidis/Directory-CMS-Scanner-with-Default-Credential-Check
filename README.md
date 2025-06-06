# 🕵️‍♂️ Directory & CMS Scanner with Default Credential Check

This tool scans website URL structures, detects CMS platforms, identifies login pages, attempts default credentials, and supports verbose mode, Tor proxy, and more.

## 📦 Requirements

- Python 3.7+
- Install required libraries::

  pip install requests beautifulsoup4 tqdm

## 🚀 Usage

python3 scanner.py --url http://example.com --wordlist wordlist.txt

## 🧰 Options

Flag				Description
--url			Base URL to scan
--wordlist		List of paths to scan
--threads		Number of concurrent threads (default: 5)
--max-depth		Recursion depth
--delay			Delay between requests
--proxy			Proxy (e.g., http://127.0.0.1:8080)
--use-tor		Use Tor proxy (127.0.0.1:9050)	
--verbose		Enable detailed logging

## 📄 Examples

Basic scan: 
* python3 scanner.py --url http://target.com --wordlist wordlist.txt
With Tor and verbose mode: 
* python3 scanner.py --url http://target.onion --wordlist wordlist.txt --use-tor --verbose


## 💡 Features

* CMS detection: WordPress, Joomla, Drupal, Magento, PrestaShop, Shopify
* Login page detection via HTML parsing
* Default credential testing
* Extraction of hidden input fields from forms
* Output to CSV (found_paths.csv)
* Tor and proxy support

## 📁 Output Files

* found_paths.csv: Successful detections
* scan_log.txt: Log and error output