"""report 핸들러의 통계 계산 로직 테스트."""

from conftest import load_handler

report = load_handler("report")


def test_empty_history_returns_zeros():
    stats = report.compute_stats([])
    assert stats == {
        "total_checks": 0,
        "uptime_pct": None,
        "avg_latency_ms": None,
        "incidents": 0,
    }


def test_all_up_is_100_percent():
    items = [
        {"status": "UP", "latency_ms": 100},
        {"status": "UP", "latency_ms": 200},
    ]
    stats = report.compute_stats(items)
    assert stats["total_checks"] == 2
    assert stats["uptime_pct"] == 100.0
    assert stats["avg_latency_ms"] == 150
    assert stats["incidents"] == 0


def test_mixed_up_and_down():
    items = [
        {"status": "UP", "latency_ms": 100},
        {"status": "DOWN", "latency_ms": None},
        {"status": "UP", "latency_ms": 300},
        {"status": "DOWN", "latency_ms": None},
    ]
    stats = report.compute_stats(items)
    assert stats["total_checks"] == 4
    assert stats["uptime_pct"] == 50.0
    assert stats["avg_latency_ms"] == 200  # latency 가 있는 항목만 평균
    assert stats["incidents"] == 2
