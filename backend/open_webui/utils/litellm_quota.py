from __future__ import annotations

import logging
from typing import Optional

import aiohttp
from aiocache import cached
from open_webui.env import AIOHTTP_CLIENT_SESSION_SSL, AIOHTTP_CLIENT_TIMEOUT, LITELLM_QUOTA_CACHE_TTL
from open_webui.models.config import Config
from open_webui.utils.tools import bearer_auth_header
from pydantic import BaseModel

log = logging.getLogger(__name__)


class LiteLLMQuotaInfo(BaseModel):
    available: bool
    has_usage: bool
    spend: float = 0.0
    max_budget: Optional[float] = None
    budget_duration: Optional[str] = None
    budget_reset_at: Optional[str] = None


@cached(
    ttl=LITELLM_QUOTA_CACHE_TTL,
    key_builder=lambda _func, base_url, api_key, budget_id: f'litellm_default_budget_{budget_id}',
)
async def _get_default_budget(base_url: str, api_key: str, budget_id: str) -> Optional[dict]:
    headers = bearer_auth_header(api_key)
    try:
        async with aiohttp.ClientSession(
            trust_env=True,
            timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT),
        ) as session:
            async with session.get(
                f'{base_url}/budget/list',
                headers=headers,
                ssl=AIOHTTP_CLIENT_SESSION_SSL,
            ) as resp:
                if not resp.ok:
                    log.warning(f'LiteLLM /budget/list returned {resp.status}')
                    return None
                budgets = await resp.json()
    except Exception as e:
        log.warning(f'Failed to fetch LiteLLM default budget: {e}')
        return None

    for budget in budgets or []:
        if budget.get('budget_id') == budget_id:
            return budget
    return None


@cached(
    ttl=LITELLM_QUOTA_CACHE_TTL,
    key_builder=lambda _func, end_user_id: f'litellm_quota_{end_user_id}',
)
async def get_litellm_end_user_quota(end_user_id: str) -> LiteLLMQuotaInfo:
    values = await Config.get_many(
        'litellm_quota.enable',
        'litellm_quota.base_url',
        'litellm_quota.api_key',
        'litellm_quota.default_budget_id',
    )
    enabled = values.get('litellm_quota.enable')
    base_url = (values.get('litellm_quota.base_url') or '').rstrip('/')
    api_key = values.get('litellm_quota.api_key') or ''
    default_budget_id = values.get('litellm_quota.default_budget_id') or ''

    if not enabled or not base_url or not api_key:
        return LiteLLMQuotaInfo(available=False, has_usage=False)

    headers = bearer_auth_header(api_key)
    try:
        async with aiohttp.ClientSession(
            trust_env=True,
            timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT),
        ) as session:
            async with session.get(
                f'{base_url}/customer/info',
                params={'end_user_id': end_user_id},
                headers=headers,
                ssl=AIOHTTP_CLIENT_SESSION_SSL,
            ) as resp:
                if resp.status == 404:
                    # No LiteLLM "customer" record yet - the user hasn't sent a
                    # chat through the proxy, so there's nothing to report yet.
                    return LiteLLMQuotaInfo(available=True, has_usage=False)
                if not resp.ok:
                    log.warning(
                        f'LiteLLM /customer/info returned {resp.status} for end_user_id={end_user_id}'
                    )
                    return LiteLLMQuotaInfo(available=False, has_usage=False)
                data = await resp.json()
    except Exception as e:
        log.warning(f'Failed to reach LiteLLM for quota lookup: {e}')
        return LiteLLMQuotaInfo(available=False, has_usage=False)

    budget_table = data.get('litellm_budget_table') or {}
    if not budget_table and default_budget_id:
        # LiteLLM applies litellm_settings.max_end_user_budget_id in-memory on
        # every request but only persists it to the DB for end-users created
        # via POST /customer/new - implicitly-created users (the normal case
        # here) always come back with litellm_budget_table=null even though
        # the default budget is genuinely being enforced. Fall back to it.
        default_budget = await _get_default_budget(base_url, api_key, default_budget_id)
        if default_budget:
            budget_table = default_budget

    return LiteLLMQuotaInfo(
        available=True,
        has_usage=True,
        spend=float(data.get('spend') or 0.0),
        max_budget=budget_table.get('max_budget'),
        budget_duration=budget_table.get('budget_duration'),
        budget_reset_at=budget_table.get('budget_reset_at'),
    )


async def clear_litellm_quota_cache():
    await get_litellm_end_user_quota.cache.clear()
