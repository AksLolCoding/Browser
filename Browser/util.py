import re
import html
from classes import *

url_regex = re.compile("((http|https|file)://)?([a-z0-9][a-z0-9\-_~\/:\?#\[\]@!$&\'\(\)\*+,;=]*)(\.[a-z0-9\-_~\/:\?#\[\]@!$&\'\(\)\*+,;=]+)+")

def is_file(url):
    if url.startswith("file://"):
        return True
    else:
        return False

def is_custom_scheme(url):
    return url.startswith("browser://") or url.startswith("chrome://")

def check_url(url):
    if url.startswith("file://"):
        return True
    return url_regex.match(url) is not None

def google_url(search):
    return f"https://google.com/search?q={html.escape(search.replace(' ', '+'))}"

def navigate_url(url: str):
    if is_file(url):
        return "file:///" + url[7:].removeprefix("file://").replace('\\', '/')
    elif is_custom_scheme(url):
        return url
    elif check_url(url):
        return url
    else:
        return google_url(url)

def shorten(string, max):
    return string if len(string) < max else f"{string[0:max-3]}..."

if __name__ == "__main__":
    res = navigate_url(r"file://C:\Users\aksha\Downloads\dummy.pdf")
    print(res)