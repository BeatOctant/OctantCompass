"""Whether a newer OctantCompass is out (OctantSpecs decisions.md, 配布): the window shows a link to its
release page, and `serve` says so in the log (and on the terminal it runs on). Nothing is fetched or installed; there
is no automatic update in the Dev stage (OctantSpecs constitution.md, 10).

The setting release_url is GitHub's API for the latest release (null: no check). Its tag_name is compared with this
version, and its html_url is the page the link opens. It is asked once when the window opens or `serve` starts, then
once a day while it stays open or running. Any failure (no network, no release, a version that does not read) shows
nothing and never stops OctantCompass.
"""

import json
import re
import threading
from urllib.parse import urlsplit
from urllib.request import Request

from . import __version__
from .dbupdate import USER_AGENT, urlopen

CHECK_SECONDS = 24 * 60 * 60
TIMEOUT_SECONDS = 10
# The API's answer is a few kilobytes plus the release notes; more is not a release.
MAX_BYTES = 1 << 20


def version_numbers(text):
    """"v0.2.4" or "0.2.4" -> (0, 2, 4); None for anything else (a pre-release suffix, "unknown")."""
    match = re.fullmatch(r"v?(\d+(?:\.\d+)*)", text if isinstance(text, str) else "")
    if not match:
        return None
    numbers = [int(part) for part in match.group(1).split(".")]
    while len(numbers) > 1 and numbers[-1] == 0:
        numbers.pop()  # 0.3 and 0.3.0 are the same version
    return tuple(numbers)


def release_page(url):
    """Whether url may be the link the window opens: an https page on github.com, where releases are. The answer is
    not signed, so a link elsewhere is not shown."""
    parts = urlsplit(url)
    return parts.scheme.lower() == "https" and parts.hostname == "github.com" and parts.port is None


def latest_release(url, timeout=TIMEOUT_SECONDS):
    """GitHub's answer for the latest release (GET /repos/{owner}/{repo}/releases/latest): {"tag_name", "html_url",
    ...}. Over https only, redirects included (dbupdate.urlopen)."""
    if urlsplit(url).scheme.lower() != "https":
        raise ValueError("not an https URL")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json",
                                    "X-GitHub-Api-Version": "2022-11-28"})
    with urlopen(request, timeout=timeout) as response:
        if urlsplit(response.geturl()).scheme.lower() != "https":
            raise ValueError("redirected away from https")
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("the answer is too large")
    return json.loads(body)


def newer_release(url, *, current=__version__, fetch=latest_release):
    """{"version": the latest release's version, "url": its page} when it is newer than this one, else None. Never
    raises: a check that fails says nothing."""
    try:
        if not url or version_numbers(current) is None:
            return None
        release = fetch(url)
        latest = version_numbers(release.get("tag_name"))
        page = release.get("html_url")
        if latest is None or latest <= version_numbers(current):
            return None
        if not isinstance(page, str) or not release_page(page):
            return None
        return {"version": release["tag_name"].lstrip("v"), "url": page}
    except Exception:  # noqa: BLE001 - a version notice must never stop OctantCompass
        return None


def watch(check, found, stop=None, every=CHECK_SECONDS):
    """Run check() now and then every `every` seconds until stop (a threading.Event) is set; found(result) gets each
    newer release, once per version. Meant for a daemon thread."""
    stop = stop or threading.Event()
    told = None
    while True:
        result = check()
        if result is not None and result["version"] != told:
            told = result["version"]
            found(result)
        if stop.wait(every):
            return
