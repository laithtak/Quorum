"""Tests for ConversationMemory."""

from council.memory import ConversationMemory


def test_add_exchange_and_context():
    mem = ConversationMemory()
    mem.add_exchange("Hello", "Hi there")
    ctx = mem.get_context()
    assert len(ctx) == 2
    assert ctx[0].role == "user"
    assert ctx[0].content == "Hello"
    assert ctx[1].role == "assistant"
    assert ctx[1].content == "Hi there"


def test_clear():
    mem = ConversationMemory()
    mem.add_exchange("Q", "A")
    mem.clear()
    assert mem.get_context() == []


def test_rolling_summary_when_over_limit():
    mem = ConversationMemory(max_tokens=50)
    mem.add_exchange("A" * 200, "B" * 200)
    mem.add_exchange("C" * 200, "D" * 200)
    ctx = mem.get_context()
    assert any(m.role == "system" and "Prior conversation summary" in m.content for m in ctx)


def test_to_dict_roundtrip():
    mem = ConversationMemory(max_tokens=4000)
    mem.add_exchange("q1", "r1")
    mem.add_exchange("q2", "r2")
    data = mem.to_dict()
    restored = ConversationMemory.from_dict(data)
    assert restored.get_context() == mem.get_context()


def test_multiple_exchanges_order():
    mem = ConversationMemory()
    for i in range(3):
        mem.add_exchange(f"q{i}", f"r{i}")
    ctx = mem.get_context()
    assert [m.content for m in ctx] == ["q0", "r0", "q1", "r1", "q2", "r2"]
