"""Fetch recent NASA pages mentioning 'Artemis' and save top pages to artifacts/nasa_artemis_pages.json

This is a best-effort scraper: it queries NASA search and fetches several result pages.
"""
import requests
# === AGL auto-injected knobs (idempotent) ===
try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
_AGL_PREVIEW_20 = _to_int('AGL_PREVIEW_20', 20)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import json
import re
import os
import time
import logging
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
BASE = 'https://www.nasa.gov'
SEARCH_PATHS = [BASE + '/search?q=Artemis', BASE + '/search?query=Artemis', BASE + '/search?keyword=Artemis', BASE + '/search?language=en&query=Artemis']
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger('fetch_nasa_artemis')
DEFAULT_HEADERS = {'User-Agent': 'AGLHarvester/1.0 (+https://github.com/OWNER/REPO)'}
def make_session(retries=3, backoff_factor=0.6, status_forcelist=(429, 500, 502, 503, 504)):
    s = requests.Session()
    retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor, status_forcelist=status_forcelist, raise_on_status=False)
    adapter = HTTPAdapter(max_retries=retry)
    s.mount('http://', adapter)
    s.mount('https://', adapter)
    s.headers.update(DEFAULT_HEADERS)
    return s
def find_links(html):
    hrefs = re.findall('href=["\\\']([^"\\\']+)["\\\']', html)
    good = []
    for h in hrefs:
        if h.startswith('/') and ('/press-release' in h or '/feature' in h or '/news' in h or ('/mission' in h.lower())):
            full = urljoin(BASE, h)
            if full not in good:
                good.append(full)
    return good
def fetch_page(session, url, timeout=15):
    try:
        r = session.get(url, timeout=timeout)
        if r.status_code == 403:
            return {'url': url, 'error': f'403 Forbidden (maybe robots or blocking)'}
        r.raise_for_status()
        text = r.text
        title = re.search('<title>(.*?)</title>', text, re.I | re.S)
        title = title.group(1).strip() if title else url
        body = ''
        m = re.search('<main.*?>(.*?)</main>', text, re.I | re.S)
        if m:
            body = re.sub('<[^>]+>', '', m.group(1))
        else:
            ps = re.findall('<p[^>]*>(.*?)</p>', text, re.I | re.S)
            body = '\n\n'.join([re.sub('<[^>]+>', '', p).strip() for p in ps[:_AGL_PREVIEW_20]])
        return {'url': url, 'title': title, 'text': body}
    except Exception as e:
        return {'url': url, 'error': str(e)}
def main():
    LOG.info('Querying NASA search for Artemis...')
    session = make_session()
    html = None
    for s in SEARCH_PATHS:
        try:
            LOG.info('Trying search URL: %s', s)
            r = session.get(s, timeout=15)
            if r.status_code == 403:
                LOG.error('Search returned 403 for %s - site may block automated scrapers', s)
                continue
            if r.status_code == 404:
                LOG.warning('Search returned 404 for %s - trying next pattern', s)
                continue
            r.raise_for_status()
            html = r.text
            LOG.info('Search URL %s succeeded', s)
            break
        except Exception as e:
            LOG.warning('Search attempt %s failed: %s', s, e)
            continue
    if not html:
        LOG.error('All search URL patterns failed; aborting fetch.')
        return
    links = find_links(html)
    LOG.info('Found %d candidate links; fetching top %d...', len(links), min(5, len(links)))
    pages = []
    outdir = os.path.join(os.path.dirname(__file__), '..', 'artifacts')
    outdir = os.path.abspath(outdir)
    os.makedirs(outdir, exist_ok=True)
    for url in links[:5]:
        LOG.info('Fetching %s', url)
        p = fetch_page(session, url)
        pages.append(p)
        time.sleep(1.0)
    outp = os.path.join(outdir, 'nasa_artemis_pages.json')
    with open(outp, 'w', encoding='utf-8') as fh:
        json.dump(pages, fh, ensure_ascii=False, indent=2)
    LOG.info('Saved pages to %s', outp)
if __name__ == '__main__':
    main()
