from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from .models import PluginConfig


class FeishuAPIError(RuntimeError):
    pass


@dataclass(slots=True)
class TokenState:
    token: str = ""
    expires_at: float = 0.0


class FeishuOpenAPIClient:
    def __init__(self, config: PluginConfig):
        self.config = config
        self._token_state = TokenState()

    @property
    def open_base(self) -> str:
        brand = self.config.brand.strip()
        if brand.startswith("https://"):
            return brand.rstrip("/")
        if brand == "lark":
            return "https://open.larksuite.com"
        return "https://open.feishu.cn"

    def is_configured(self) -> bool:
        return bool(self.config.app_id and self.config.app_secret)

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        json_body: Any | None = None,
        extra_headers: dict[str, str] | None = None,
        retry_on_auth_error: bool = True,
    ) -> dict[str, Any]:
        if not self.is_configured():
            raise FeishuAPIError("Missing app_id/app_secret in plugin config.")

        token = await self._get_tenant_access_token(force_refresh=False)
        url = self._build_url(path, query)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        if extra_headers:
            headers.update(extra_headers)

        status_code, data = await self._json_request(method.upper(), url, headers=headers, json_body=json_body)
        if status_code in {401, 403} and retry_on_auth_error:
            self._token_state = TokenState()
            return await self.request(
                method,
                path,
                query=query,
                json_body=json_body,
                extra_headers=extra_headers,
                retry_on_auth_error=False,
            )
        if status_code >= 400:
            raise FeishuAPIError(f"HTTP {status_code}: {data}")

        code = data.get("code")
        if code not in (None, 0):
            raise FeishuAPIError(f"Feishu API error code={code} msg={data.get('msg') or data.get('message')}")
        return data

    async def _get_tenant_access_token(self, force_refresh: bool) -> str:
        now = time.time()
        if not force_refresh and self._token_state.token and now < self._token_state.expires_at:
            return self._token_state.token

        payload = {"app_id": self.config.app_id, "app_secret": self.config.app_secret}
        url = self._build_url("/open-apis/auth/v3/tenant_access_token/internal")
        status_code, data = await self._json_request("POST", url, headers={"Content-Type": "application/json; charset=utf-8"}, json_body=payload)
        if status_code >= 400:
            raise FeishuAPIError(f"Auth HTTP {status_code}: {data}")
        token = data.get("tenant_access_token") or ""
        if not token:
            raise FeishuAPIError(f"Failed to get tenant_access_token: {data}")
        expire = int(data.get("expire", 7200) or 7200)
        self._token_state = TokenState(token=token, expires_at=time.time() + max(60, expire - 120))
        return token

    def _build_url(self, path: str, query: dict[str, Any] | None = None) -> str:
        normalized = path if path.startswith("/") else f"/{path}"
        url = urljoin(f"{self.open_base}/", normalized.lstrip("/"))
        if query:
            encoded = urlencode([(key, value) for key, value in query.items()], doseq=True)
            if encoded:
                url = f"{url}?{encoded}"
        return url

    async def _json_request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json_body: Any | None = None,
    ) -> tuple[int, dict[str, Any]]:
        return await asyncio.to_thread(self._sync_json_request, method, url, headers, json_body)

    @staticmethod
    def _sync_json_request(
        method: str,
        url: str,
        headers: dict[str, str],
        json_body: Any | None,
    ) -> tuple[int, dict[str, Any]]:
        body_bytes = None
        if json_body is not None:
            body_bytes = json.dumps(json_body, ensure_ascii=False).encode("utf-8")

        request = Request(url=url, data=body_bytes, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                status_code = getattr(response, "status", response.getcode())
                text = response.read().decode("utf-8")
        except HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            return exc.code, FeishuOpenAPIClient._parse_json_text(text)
        except URLError as exc:
            raise FeishuAPIError(f"Network error: {exc}") from exc

        return status_code, FeishuOpenAPIClient._parse_json_text(text)

    @staticmethod
    def _parse_json_text(text: str) -> dict[str, Any]:
        try:
            data = json.loads(text)
        except ValueError as exc:
            raise FeishuAPIError(f"Non-JSON response: {text[:1000]}") from exc
        if not isinstance(data, dict):
            raise FeishuAPIError(f"Unexpected response payload: {data}")
        return data
