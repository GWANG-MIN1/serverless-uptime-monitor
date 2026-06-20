"""register 핸들러의 URL 검증 로직 테스트."""

from conftest import load_handler

register = load_handler("register")


def test_valid_http_and_https_urls():
    assert register.is_valid_url("http://example.com")
    assert register.is_valid_url("https://example.com/path?q=1")


def test_url_with_surrounding_spaces_is_valid():
    # 앞뒤 공백은 무시하고 검증한다.
    assert register.is_valid_url("  https://example.com  ")


def test_invalid_urls_are_rejected():
    assert not register.is_valid_url("example.com")        # 스킴 없음
    assert not register.is_valid_url("ftp://example.com")  # 허용되지 않는 스킴
    assert not register.is_valid_url("https://")           # 호스트 없음
    assert not register.is_valid_url("")
    assert not register.is_valid_url(None)
