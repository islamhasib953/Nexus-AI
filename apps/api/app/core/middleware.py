import re
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.logging import request_id_context

_request_id_pattern = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def configure_request_id(value: str | None) -> str:
    if value and _request_id_pattern.fullmatch(value):
        return value
    return str(uuid.uuid4())


class CorrelationIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        raw_request_id = headers.get(b"x-request-id", b"").decode("latin-1") or None
        request_id = configure_request_id(raw_request_id)
        scope.setdefault("state", {})["request_id"] = request_id
        token = request_id_context.set(request_id)

        async def send_with_correlation(message: dict) -> None:
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                response_headers.append((b"x-request-id", request_id.encode("ascii")))
                message = {**message, "headers": response_headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_correlation)
        finally:
            request_id_context.reset(token)


def request_id_from_request(request: Request) -> str:
    return getattr(request.state, "request_id", request_id_context.get())


async def attach_request_state(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request.state.request_id = request_id_context.get()
    return await call_next(request)
