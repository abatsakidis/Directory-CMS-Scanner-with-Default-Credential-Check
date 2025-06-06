# 🕵️‍♂️ Directory & CMS Scanner with Default Credential Check

This tool scans website URL structures, detects CMS platforms, identifies login pages, attempts default credentials, and supports verbose mode, Tor proxy, and more.

## 📦 Requirements

- Python 3.7+
- Install required libraries:< br / >

  pip install requests beautifulsoup4 tqdm

## 🚀 Usage

python3 scanner.py --url http://example.com --wordlist wordlist.txt

## 🧰 Options

Flag				Description< br / >
--url			Base URL to scan< br / >
--wordlist		List of paths to scan< br / >
--threads		Number of concurrent threads (default: 5)< br / >
--max-depth		Recursion depth< br / >
--delay			Delay between requests< br / >
--proxy			Proxy (e.g., http://127.0.0.1:8080)< br / >
--use-tor		Use Tor proxy (127.0.0.1:9050)	< br / >
--verbose		Enable detailed logging< br / >

## 📄 Examples

Basic scan: < br / >
* python3 scanner.py --url http://target.com --wordlist wordlist.txt< br / >
With Tor and verbose mode: < br / >
* python3 scanner.py --url http://target.onion --wordlist wordlist.txt --use-tor --verbose< br / >


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