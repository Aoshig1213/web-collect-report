"""ページの取得。robots.txt を守り、間隔をあけ、一時的なエラーは再試行する。"""

from __future__ import annotations

import logging
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)


class FetchError(Exception):
    """ページが取れなかったとき（再試行しても失敗、または robots.txt で禁止）。"""


class Fetcher:
    def __init__(self, user_agent: str, delay_seconds: float, timeout_seconds: float, max_retries: int,
                 sleep=time.sleep):
        self.delay = delay_seconds
        self.timeout = timeout_seconds
        self._sleep = sleep
        self._last = 0.0
        self._robots: dict[str, RobotFileParser] = {}
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent
        retry = Retry(total=max_retries, backoff_factor=1.0, status_forcelist=(429, 500, 502, 503, 504),
                      allowed_methods=("GET",), respect_retry_after_header=True)
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.count = 0

    def _wait(self) -> None:
        # 前のリクエストから delay 秒たつまで待つ
        rest = self.delay - (time.monotonic() - self._last)
        if self._last and rest > 0:
            self._sleep(rest)
        self._last = time.monotonic()

    def _robots_for(self, url: str) -> RobotFileParser:
        p = urlparse(url)
        root = f"{p.scheme}://{p.netloc}/"
        if root not in self._robots:
            rp = RobotFileParser()
            robots_url = urljoin(root, "robots.txt")
            self._wait()
            try:
                r = self.session.get(robots_url, timeout=self.timeout)
            except requests.RequestException as e:
                raise FetchError(f"robots.txt を確認できませんでした: {e}") from e
            if r.status_code == 200:
                rp.parse(r.text.splitlines())
            elif r.status_code in (401, 403):
                rp.disallow_all = True  # 読めないときは禁止として扱う（安全側）
            else:
                rp.allow_all = True  # 404 など: robots.txt なし＝制限なし
            log.info("robots.txt を確認しました: %s（%s）", robots_url, r.status_code)
            self._robots[root] = rp
        return self._robots[root]

    def get(self, url: str) -> str:
        if not self._robots_for(url).can_fetch(self.user_agent, url):
            raise FetchError(f"robots.txt で取得が禁止されています: {url}")
        self._wait()
        try:
            r = self.session.get(url, timeout=self.timeout)
            r.raise_for_status()
        except requests.RequestException as e:
            raise FetchError(f"取得に失敗しました: {url}（{e}）") from e
        self.count += 1
        r.encoding = r.encoding if r.encoding and r.encoding.lower() != "iso-8859-1" else "utf-8"
        return r.text
