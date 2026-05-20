"""Streamlit 환경에서 견고한 asyncio event loop 운영.

Streamlit 은 매 rerun 마다 main thread 에서 스크립트를 다시 실행한다. 핸들러에서
`asyncio.run(coro)` 를 호출하면 매번 새 event loop 가 만들어졌다가 닫힌다.
RAGAnything/LightRAG 의 worker pool (임베딩/LLM async 큐) 은 처음 init 된 loop 에
묶이므로, 두 번째 호출에서 다른 loop 가 들어오면 임베딩 worker 가

    "<PriorityQueue at 0x...> is bound to a different event loop"

로 죽는다. 그러면 청크/엔티티가 한 건도 안 만들어진 채 인제스트가 끝나고,
`doc_status` 만 `processed` 로 마킹되어 채팅이 영구히 "no-context" 로 떨어진다.
이 모듈은 그걸 막기 위한 모듈-레벨 단일 loop 이다.
"""
from __future__ import annotations

import asyncio
from typing import Any, Coroutine, TypeVar

_T = TypeVar("_T")

_loop: asyncio.AbstractEventLoop | None = None


def get_loop() -> asyncio.AbstractEventLoop:
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop


def run(coro: Coroutine[Any, Any, _T]) -> _T:
    """Streamlit 핸들러에서 `asyncio.run()` 대신 호출한다."""
    return get_loop().run_until_complete(coro)
