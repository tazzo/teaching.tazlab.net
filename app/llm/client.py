"""The OpenAI-compatible provider client for the LLM-assisted variant path.

Contract verified live against `https://opencode.ai/zen/go/v1` (DESIGN §2.5):

* the required ``x-opencode-session`` header — without it the provider answers HTTP 400
  ``MissingSessionID``; a stable per-process id is enough and shares one prompt-cache
  bucket;
* ``reasoning_effort: "none"`` — without it a small token budget is eaten by reasoning and
  ``content`` comes back empty;
* **no provider-side JSON schema** (``response_format: json_schema`` → HTTP 400), so the
  spec is prompt-enforced, parsed and validated here, and retried within a bounded budget;
* a per-call timeout and a concurrency cap, so a burst cannot exhaust a shared quota.

The client **never raises on provider failure**: it returns an empty spec list plus a
machine reason, and the caller degrades to the deterministic template generator. The API
key is read from the environment, sent in the ``Authorization`` header, and never logged.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass

import httpx

from app.llm import spec as spec_module
from app.llm.spec import Spec

logger = logging.getLogger("teaching.llm")

DEFAULT_BASE_URL = "https://opencode.ai/zen/go/v1"
DEFAULT_MODEL = "deepseek-v4.1-flash"
DEFAULT_REASONING_EFFORT = "none"
DEFAULT_TIMEOUT = 20.0
DEFAULT_MAX_CONCURRENCY = 4
MAX_CALL_ATTEMPTS = 2
MAX_TOKENS = 2048

# Stable for the life of the process: the provider routes on it and reuses one prompt
# cache bucket (the pattern Hindsight uses). Never a secret, never a per-request value.
SESSION_ID = os.getenv("TEACHING_LLM_SESSION_ID") or uuid.uuid4().hex


class ProviderError(RuntimeError):
    """A provider-side failure, reduced to a machine reason for the log line."""

    def __init__(self, reason: str, detail: str | None = None, *, retryable: bool = False) -> None:
        super().__init__(reason if detail is None else f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail
        self.retryable = retryable


@dataclass(frozen=True)
class ProviderConfig:
    base_url: str
    model: str
    api_key: str | None
    session_id: str
    reasoning_effort: str
    timeout: float
    max_concurrency: int

    @classmethod
    def from_env(cls) -> ProviderConfig:
        return cls(
            base_url=os.getenv("TEACHING_LLM_BASE_URL", DEFAULT_BASE_URL),
            model=os.getenv("TEACHING_LLM_MODEL", DEFAULT_MODEL),
            api_key=os.getenv("OPENCODE_API_KEY") or None,
            session_id=SESSION_ID,
            reasoning_effort=os.getenv("TEACHING_LLM_REASONING_EFFORT", DEFAULT_REASONING_EFFORT),
            timeout=float(os.getenv("TEACHING_LLM_TIMEOUT", str(DEFAULT_TIMEOUT))),
            max_concurrency=int(os.getenv("TEACHING_LLM_MAX_CONCURRENCY", str(DEFAULT_MAX_CONCURRENCY))),
        )

    def safe(self) -> dict[str, object]:
        """The configuration as it may appear in a log line — no key material."""
        return {
            "base_url": self.base_url,
            "model": self.model,
            "session_id": self.session_id,
            "reasoning_effort": self.reasoning_effort,
            "timeout": self.timeout,
            "max_concurrency": self.max_concurrency,
            "api_key_set": bool(self.api_key),
        }


@dataclass(frozen=True)
class SpecFetch:
    """The outcome of one provider call: what survived, and why it degraded."""

    specs: tuple[Spec, ...]
    error: str | None = None           # provider failure class, or None
    rejected: tuple[str, ...] = ()     # one machine reason per rejected spec
    attempts: int = 0

    @property
    def degraded(self) -> bool:
        return not self.specs


class LLMClient:
    """One provider call returns N specs (DESIGN §2.5)."""

    def __init__(
        self,
        config: ProviderConfig | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config or ProviderConfig.from_env()
        self._transport = transport
        self._client = client
        self._owns_client = client is None
        self._semaphore = asyncio.Semaphore(max(1, self.config.max_concurrency))

    # ------------------------------------------------------------------ plumbing
    async def __aenter__(self) -> LLMClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                transport=self._transport,
            )
        return self._client

    async def aclose(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    # --------------------------------------------------------------------- call
    def _request(self) -> tuple[str, dict, dict]:
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "x-opencode-session": self.config.session_id,
            "Content-Type": "application/json",
        }
        body: dict[str, object] = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": None}],  # filled per call
            "max_tokens": MAX_TOKENS,
            "temperature": 0.7,
        }
        if self.config.reasoning_effort:
            body["reasoning_effort"] = self.config.reasoning_effort
        return url, headers, body

    async def _complete(self, prompt: str) -> str:
        """One HTTP round trip; raises :class:`ProviderError` on anything unexpected."""
        if not self.config.api_key:
            raise ProviderError("missing_api_key")

        url, headers, body = self._request()
        body["messages"] = [{"role": "user", "content": prompt}]

        async with self._semaphore:
            try:
                response = await self._http().post(url, json=body, headers=headers)
            except httpx.TimeoutException as exc:
                raise ProviderError("provider_timeout", type(exc).__name__, retryable=True) from exc
            except httpx.HTTPError as exc:
                raise ProviderError(f"transport_error:{type(exc).__name__}", retryable=True) from exc

        if response.status_code >= 500:
            raise ProviderError(f"http_{response.status_code}", retryable=True)
        if response.status_code >= 400:
            # 400 MissingSessionID lives here: retrying it would be pointless.
            raise ProviderError(f"http_{response.status_code}", response.text[:200])

        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError("malformed_response", type(exc).__name__) from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("empty_content", retryable=True)
        return content

    async def fetch_outcome(self, scenario_id: str, difficulty: str, count: int) -> SpecFetch:
        """Fetch and validate N specs. Never raises; never logs the key."""
        declared = spec_module.scenario(scenario_id)
        if declared is None:
            return SpecFetch((), "unknown_scenario")
        if count < 1:
            return SpecFetch((), "invalid_count")

        prompt = spec_module.prompt(scenario_id, count)
        rejected: tuple[str, ...] = ()
        error: str | None = None
        attempts = 0
        for attempts in range(1, MAX_CALL_ATTEMPTS + 1):
            # INFO on the provider call (DESIGN §2.11) — configuration, never the key.
            logger.info(
                "llm provider call",
                extra={"scenario": scenario_id, "difficulty": difficulty, "count": count,
                       "attempt": attempts, **self.config.safe()},
            )
            try:
                content = await self._complete(prompt)
            except ProviderError as exc:
                error = exc.reason
                logger.warning(
                    "llm provider call failed",
                    extra={"scenario": scenario_id, "attempt": attempts,
                           "provider_error": exc.reason},
                )
                if not exc.retryable:
                    break
                continue

            # A successful round trip clears any earlier failure: what remains is a
            # *spec* problem, which the caller reports as invalid_specs:N, not as an outage.
            error = None
            specs, rejected = spec_module.parse_specs(content, scenario_id)
            if specs:
                return SpecFetch(tuple(specs[:count]), None, tuple(rejected), attempts)
            logger.warning(
                "llm answer carried no valid spec",
                extra={"scenario": scenario_id, "attempt": attempts,
                       "rejected": list(rejected)[:8], "rejected_count": len(rejected)},
            )

        if error is None and not rejected:
            error = "no_valid_spec"
        return SpecFetch((), error, rejected, attempts)


# ------------------------------------------------------------------ public surface
_default: LLMClient | None = None


def default_client() -> LLMClient:
    global _default
    if _default is None:
        _default = LLMClient()
    return _default


async def fetch_variant_specs(
    scenario: str,
    difficulty: str,
    count: int,
    *,
    client: LLMClient | None = None,
) -> list[Spec]:
    """One provider call → the specs that survived validation. Empty means degraded.

    Never raises on provider failure: the caller falls back to the template generator and
    says so. Use :func:`fetch_variant_specs_report` when the reason is needed.
    """
    outcome = await fetch_variant_specs_report(scenario, difficulty, count, client=client)
    return list(outcome.specs)


async def fetch_variant_specs_report(
    scenario: str,
    difficulty: str,
    count: int,
    *,
    client: LLMClient | None = None,
) -> SpecFetch:
    impl = client or default_client()
    return await impl.fetch_outcome(scenario, difficulty, count)
