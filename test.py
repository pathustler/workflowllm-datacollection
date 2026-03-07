import requests


url = "https://www.manualslib.com/manual/2344470/Abb-Irb-6400r.html#product-IRB 6400R/2.8-200"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
}


PROXY = "http://adgkwbzb:43oaua4v9w5g@31.59.20.176:6754"

PROXIES = {
    "http": PROXY,
    "https": PROXY
}


print("Status Code:", requests.get(url, headers=HEADERS).status_code)