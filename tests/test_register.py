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


# ── SSRF 가드 (upgrade-05) ──────────────────────────────────────────────────


def test_blocks_private_and_reserved_ip_literals():
    # IP 리터럴은 DNS 없이 바로 판정된다.
    assert register.is_blocked_host("http://127.0.0.1")            # 루프백
    assert register.is_blocked_host("http://10.0.0.5")            # 사설
    assert register.is_blocked_host("http://192.168.1.1")        # 사설
    assert register.is_blocked_host("http://169.254.169.254")    # 링크로컬(IMDS)
    assert register.is_blocked_host("http://[::1]")              # IPv6 루프백


def test_allows_public_ip_literal():
    assert not register.is_blocked_host("http://8.8.8.8")


def test_ip_is_blocked_helper():
    assert register._ip_is_blocked("169.254.169.254")
    assert not register._ip_is_blocked("1.1.1.1")
    assert not register._ip_is_blocked("not-an-ip")
