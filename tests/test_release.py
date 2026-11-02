import io
import json
import threading

import pytest

from octantcompass import release
from octantcompass.release import latest_release, newer_release, version_numbers, watch

URL = "https://api.github.com/repos/BeatOctant/OctantCompass/releases/latest"
PAGE = "https://github.com/BeatOctant/OctantCompass/releases/tag/v0.2.4"


def answer(tag="v0.2.4", page=PAGE):
    return lambda url: {"tag_name": tag, "html_url": page}


def test_versions_read_as_numbers():
    assert version_numbers("v0.2.10") > version_numbers("0.2.9")
    assert version_numbers("v0.3") == version_numbers("0.3.0")
    assert version_numbers("unknown") is None and version_numbers("v0.3.0-rc1") is None and version_numbers(None) is None


def test_a_newer_release_is_named_with_its_page():
    assert newer_release(URL, current="0.2.3", fetch=answer()) == {"version": "0.2.4", "url": PAGE}
    assert newer_release(URL, current="0.2.4", fetch=answer()) is None
    assert newer_release(URL, current="0.2.5", fetch=answer()) is None


def test_a_failed_or_turned_off_check_says_nothing():
    def fail(url):
        raise OSError("no network")

    assert newer_release(URL, current="0.2.3", fetch=fail) is None
    assert newer_release(URL, current="0.2.3", fetch=lambda url: {"message": "Not Found"}) is None
    assert newer_release(URL, current="0.2.3", fetch=lambda url: []) is None
    assert newer_release(URL, current="0.2.3", fetch=answer(tag="nightly")) is None
    assert newer_release(URL, current="0.2.3", fetch=answer(page="http://example.invalid/")) is None
    assert newer_release(URL, current="0.2.3", fetch=answer(page="https://example.invalid/releases")) is None
    assert newer_release(URL, current="0.2.3", fetch=answer(page="https://github.com.example.invalid/")) is None
    assert newer_release(URL, current="0.2.3", fetch=answer(page="https://github.com:8443/x")) is None
    assert newer_release(URL, current="0.2.3", fetch=answer(page=None)) is None
    assert newer_release(URL, current="unknown", fetch=answer(tag="v9.0.0")) is None
    assert newer_release(None, current="0.2.3", fetch=answer(tag="v9.0.0")) is None


class Response(io.BytesIO):
    def __init__(self, body, url=URL):
        super().__init__(body)
        self.url = url

    def geturl(self):
        return self.url


def test_the_latest_release_is_read_from_the_api(monkeypatch):
    asked = []
    body = json.dumps({"tag_name": "v0.2.4", "html_url": PAGE}).encode()
    monkeypatch.setattr(release, "urlopen", lambda request, timeout: asked.append(request) or Response(body))
    assert latest_release(URL) == {"tag_name": "v0.2.4", "html_url": PAGE}
    assert asked[0].get_header("User-agent").startswith("OctantCompass/")
    assert asked[0].get_header("Accept") == "application/vnd.github+json"
    with pytest.raises(ValueError):
        latest_release("http://api.github.com/repos/BeatOctant/OctantCompass/releases/latest")
    monkeypatch.setattr(release, "urlopen", lambda request, timeout: Response(b" " * (release.MAX_BYTES + 1)))
    with pytest.raises(ValueError):
        latest_release(URL)


def test_watch_checks_at_once_then_on_each_round_and_tells_each_version_once():
    results = iter([None, {"version": "0.2.4", "url": PAGE}, {"version": "0.2.4", "url": PAGE},
                    {"version": "0.2.5", "url": PAGE}])
    told = []
    stop = threading.Event()
    rounds = []

    def check():
        rounds.append(1)
        if len(rounds) == 4:
            stop.set()
        return next(results)

    watch(check, told.append, stop, every=0)
    assert len(rounds) == 4
    assert [found["version"] for found in told] == ["0.2.4", "0.2.5"]
