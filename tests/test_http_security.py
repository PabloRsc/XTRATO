import asyncio

from starlette.requests import Request
from starlette.responses import Response

from app.main import MAX_BACKUP_UPLOAD_BYTES, protect_mutations


def make_request(path, method="GET", headers=None):
    values = [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()]
    return Request({
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": "https",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": values,
        "server": ("xtrato.test", 443),
        "client": ("127.0.0.1", 12345),
        "root_path": "",
    })


def test_restore_rejects_requests_without_content_length():
    called = False

    async def call_next(_request):
        nonlocal called
        called = True
        return Response("unexpected")

    response = asyncio.run(protect_mutations(
        make_request("/api/backup/restore", method="POST", headers={"X-Xtrato-Request": "1"}),
        call_next,
    ))

    assert response.status_code == 411
    assert called is False


def test_restore_rejects_invalid_or_negative_content_length():
    async def call_next(_request):
        return Response("unexpected")

    invalid = asyncio.run(protect_mutations(
        make_request("/api/backup/restore", method="POST", headers={
            "Content-Length": "unknown",
            "X-Xtrato-Request": "1",
        }),
        call_next,
    ))
    negative = asyncio.run(protect_mutations(
        make_request("/api/backup/restore", method="POST", headers={
            "Content-Length": "-1",
            "X-Xtrato-Request": "1",
        }),
        call_next,
    ))

    assert invalid.status_code == 400
    assert negative.status_code == 400


def test_restore_rejects_body_larger_than_ten_megabytes():
    called = False

    async def call_next(_request):
        nonlocal called
        called = True
        return Response("unexpected")

    response = asyncio.run(protect_mutations(
        make_request("/api/backup/restore", method="POST", headers={
            "Content-Length": str(MAX_BACKUP_UPLOAD_BYTES + 1),
            "X-Xtrato-Request": "1",
        }),
        call_next,
    ))

    assert response.status_code == 413
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert called is False


def test_restore_accepts_bounded_same_origin_request_for_csrf_validation():
    async def call_next(_request):
        return Response("accepted by downstream")

    response = asyncio.run(protect_mutations(
        make_request("/api/backup/restore", method="POST", headers={
            "Content-Length": "1024",
            "X-Xtrato-Request": "1",
            "Host": "xtrato.test",
            "Origin": "https://xtrato.test",
        }),
        call_next,
    ))

    assert response.status_code == 200


def test_mutating_api_request_rejects_missing_csrf_header():
    async def call_next(_request):
        return Response("unexpected")

    response = asyncio.run(protect_mutations(
        make_request("/api/purchases", method="POST", headers={"Host": "xtrato.test"}),
        call_next,
    ))

    assert response.status_code == 403
    assert response.headers["Cache-Control"] == "no-store"


def test_mutating_api_request_rejects_foreign_origin():
    async def call_next(_request):
        return Response("unexpected")

    response = asyncio.run(protect_mutations(
        make_request("/api/purchases", method="POST", headers={
            "Host": "xtrato.test",
            "Origin": "https://attacker.test",
            "X-Xtrato-Request": "1",
        }),
        call_next,
    ))

    assert response.status_code == 403
    assert response.headers["Cache-Control"] == "no-store"


def test_api_responses_are_marked_private_and_non_cacheable():
    async def call_next(_request):
        return Response("private financial data")

    response = asyncio.run(protect_mutations(
        make_request("/api/entries?month=2026-11"),
        call_next,
    ))

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Vary"] == "Cookie"


def test_non_api_static_responses_do_not_receive_api_cache_policy():
    async def call_next(_request):
        return Response("public static asset")

    response = asyncio.run(protect_mutations(
        make_request("/static/app.css"),
        call_next,
    ))

    assert "Cache-Control" not in response.headers
    assert "Pragma" not in response.headers
