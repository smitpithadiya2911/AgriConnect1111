import urllib.request
import re

url = 'https://geetanjaligroupofcolleges.in/'
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read().decode('utf-8')
    logos = re.findall(r'src=["\']([^"\']*(?:logo)[^"\']*)["\']', html, re.IGNORECASE)
    print("Found logos:", set(logos))
except Exception as e:
    print("Error:", e)
