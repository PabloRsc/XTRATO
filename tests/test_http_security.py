import asyncio

from starlette.requests import Request
from starlette.responses import Response

from app.main import BackupRestoreSizeLimitMiddleware, MAX_BACKUP_UPLOAD_BYTES, protect_mutations


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


def make_scope(path, method="POST", headers=None):
    values = [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()]
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
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
    }


def run_upload(body_chunks, headers=None, max_bytes=10, path="/api/backup/restore"):
    messages = [
        {
            "type": "http.request",
            "body": chunk,
            "more_body": index < len(body_chunks) - 1,
        }
        for index, chunk in enumerate(body_chunks)
    ]
    if not messages:
        messages = [{"type": "http.request", "body": b"", "more_body": False}]
    sent = []
    app_called = False

    async def receive():
        if messages:
            return messages.pop(0)
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    async def downstream(scope, receive, send):
        nonlocal app_called
        app_called = True
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                break
            if message["type"] == "http.request" and not message.get("more_body", False):
                break
        await Response("accepted")(scope, receive, send)

    middleware = BackupRestoreSizeLimitMiddleware(downstream, max_bytes=max_bytes)
    asyncio.run(middleware(make_scope(path, headers=headers), receive, send))
    response_start = next(message for message in sent if message["type"] == "http.response.start")
    return response_start["status"], app_called


def test_restore_accepts_bounded_stream_without_content_length():
    status, app_called = run_upload([b"small", b" body"], headers={})
    assert status == 200
    assert app_called is True


def test_restore_rejects_stream_over_limit_even_without_content_length():
    status, app_called = run_upload([b"123456", b"78901"], headers={})
    assert status == 413
    assert app_called is False


def test_restore_rejects_declared_body_larger_than_ten_megabytes_before_reading():
    status, app_called = run_upload(
        [],
        headers={"Content-Length": str(MAX_BACKUP_UPLOAD_BYTES + 1)},
        max_bytes=MAX_BACKUP_UPLOAD_BYTES,
    )
    assert status == 413
    assert app_called is False


def test_restore_rejects_invalid_or_negative_content_length():
    invalid_status, _ = run_upload([], headers={"Content-Length": "unknown"})
    negative_status, _ = run_upload([], headers={"Content-Length": "-1"})
    assert invalid_status == 400
    assert negative_status == 400


def test_non_restore_requests_are_not_subject_to_backup_upload_limit():
    status, app_called = run_upload(
        [b"large body"],
        headers={},
        max_bytes=1,
        path="/api/purchases",
    )
    assert status == 200
    assert app_called is True


def test_mutating_api_request_rejects_missing_csrf_header_with_private_headers():
    async def call_next(_request):
        return Response("unexpected")

    response = asyncio.run(protect_mutations(
        make_request("/api/purchases", method="POST", headers={"Host": "xtrato.test"}),
        call_next,
    ))

    assert response.status_code == 403
    assert response.headers["Cache-Control"] == "no-store"


def test_mutating_api_request_rejects_foreign_origin_with_private_headers():
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
