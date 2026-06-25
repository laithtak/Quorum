"""Tests for token usage and cost estimation."""

from council.usage import TokenUsage, calculate_cost, COST_TABLE


def test_calculate_cost_gpt4o():
    cost = calculate_cost("gpt-4o", prompt_tokens=1000, completion_tokens=500)
    expected = (1000 * 2.50 + 500 * 10.00) / 1_000_000
    assert abs(cost - expected) < 1e-9


def test_calculate_cost_unknown_model_uses_default():
    cost = calculate_cost("unknown-model-xyz", prompt_tokens=1_000_000, completion_tokens=0)
    assert cost == 1.0


def test_token_usage_addition():
    a = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30, estimated_cost_usd=0.01)
    b = TokenUsage(prompt_tokens=5, completion_tokens=15, total_tokens=20, estimated_cost_usd=0.02)
    combined = a + b
    assert combined.prompt_tokens == 15
    assert combined.completion_tokens == 35
    assert combined.total_tokens == 50
    assert abs(combined.estimated_cost_usd - 0.03) < 1e-9


def test_cost_table_has_common_models():
    assert "gpt-4o" in COST_TABLE
    assert "claude-sonnet-4-6" in COST_TABLE


def test_ollama_zero_cost():
    cost = calculate_cost("llama3.1", prompt_tokens=10000, completion_tokens=10000)
    assert cost == 0.0
