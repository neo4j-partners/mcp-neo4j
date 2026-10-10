from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp_neo4j_cypher.server import _is_write_query


def _driver_with_query_type(query_type):
    summary = MagicMock(query_type=query_type)
    driver = MagicMock()
    driver.execute_query = AsyncMock(return_value=([], summary, []))
    return driver


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query_type", "is_write"),
    [("r", False), ("w", True), ("rw", True), ("s", True)],
)
async def test_is_write_query_by_query_type(query_type, is_write):
    driver = _driver_with_query_type(query_type)
    assert await _is_write_query("MATCH (n) RETURN n", driver, "neo4j") is is_write


@pytest.mark.asyncio
async def test_is_write_query_runs_explain():
    driver = _driver_with_query_type("r")
    await _is_write_query("MATCH (n) RETURN n", driver, "neo4j")
    driver.execute_query.assert_awaited_once_with(
        query_="EXPLAIN MATCH (n) RETURN n", database_="neo4j"
    )
