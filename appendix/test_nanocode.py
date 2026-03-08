"""Tests for Nanocode Streaming (Appendix A)."""

from nanocode import parse_sse_events, build_thought_from_events, Thought, ToolCall


# --- SSE Parsing Tests ---

def test_parse_sse_events_extracts_data_lines():
    """Verify parse_sse_events extracts JSON from data: lines."""
    raw_lines = [
        b'event: message_start',
        b'data: {"type":"message_start","message":{"usage":{"input_tokens":42}}}',
        b'',
        b'event: content_block_delta',
        b'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello"}}',
    ]
    events = parse_sse_events(raw_lines)
    assert len(events) == 2
    assert events[0]["type"] == "message_start"
    assert events[1]["type"] == "content_block_delta"


def test_parse_sse_events_skips_non_data_lines():
    """Verify non-data lines are ignored."""
    raw_lines = [
        b'event: ping',
        b': comment',
        b'',
        b'data: {"type":"message_stop"}',
    ]
    events = parse_sse_events(raw_lines)
    assert len(events) == 1


def test_parse_sse_events_handles_string_input():
    """Verify parse_sse_events works with string lines (not just bytes)."""
    raw_lines = [
        'data: {"type":"message_stop"}',
    ]
    events = parse_sse_events(raw_lines)
    assert len(events) == 1


def test_parse_sse_events_skips_malformed_json():
    """Verify malformed JSON data lines are skipped."""
    raw_lines = [
        b'data: not json',
        b'data: {"type":"message_stop"}',
    ]
    events = parse_sse_events(raw_lines)
    assert len(events) == 1
    assert events[0]["type"] == "message_stop"


# --- Thought Building Tests ---

def test_build_thought_text_only():
    """Verify text-only response is assembled correctly."""
    events = [
        {"type": "message_start", "message": {"usage": {"input_tokens": 100}}},
        {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Hello"}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": " world"}},
        {"type": "content_block_stop", "index": 0},
        {"type": "message_stop"},
    ]
    thought, tokens = build_thought_from_events(events)
    assert thought.text == "Hello world"
    assert tokens == 100
    assert not thought.tool_calls
    assert len(thought.raw_content) == 1
    assert thought.raw_content[0]["type"] == "text"


def test_build_thought_with_tool_call():
    """Verify tool call response is assembled correctly."""
    events = [
        {"type": "message_start", "message": {"usage": {"input_tokens": 200}}},
        {"type": "content_block_start", "index": 0, "content_block": {
            "type": "tool_use", "id": "tool_123", "name": "read_file"
        }},
        {"type": "content_block_delta", "index": 0, "delta": {
            "type": "input_json_delta", "partial_json": '{"path":'
        }},
        {"type": "content_block_delta", "index": 0, "delta": {
            "type": "input_json_delta", "partial_json": ' "test.py"}'
        }},
        {"type": "content_block_stop", "index": 0},
        {"type": "message_stop"},
    ]
    thought, tokens = build_thought_from_events(events)
    assert thought.text is None
    assert len(thought.tool_calls) == 1
    assert thought.tool_calls[0].name == "read_file"
    assert thought.tool_calls[0].args == {"path": "test.py"}
    assert tokens == 200


def test_build_thought_mixed_text_and_tool():
    """Verify response with both text and tool calls."""
    events = [
        {"type": "message_start", "message": {"usage": {"input_tokens": 50}}},
        {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Let me read that."}},
        {"type": "content_block_stop", "index": 0},
        {"type": "content_block_start", "index": 1, "content_block": {
            "type": "tool_use", "id": "tool_456", "name": "read_file"
        }},
        {"type": "content_block_delta", "index": 1, "delta": {
            "type": "input_json_delta", "partial_json": '{"path": "main.py"}'
        }},
        {"type": "content_block_stop", "index": 1},
        {"type": "message_stop"},
    ]
    thought, tokens = build_thought_from_events(events)
    assert thought.text == "Let me read that."
    assert len(thought.tool_calls) == 1
    assert thought.tool_calls[0].name == "read_file"
    assert len(thought.raw_content) == 2


def test_build_thought_tracks_streaming_output():
    """Verify print_fn is called for each text delta."""
    chunks = []
    events = [
        {"type": "message_start", "message": {"usage": {"input_tokens": 10}}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "one"}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": " two"}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": " three"}},
        {"type": "message_stop"},
    ]
    thought, _ = build_thought_from_events(events, print_fn=chunks.append)
    assert chunks == ["one", " two", " three"]
    assert thought.text == "one two three"


def test_build_thought_empty_response():
    """Verify empty event stream produces empty Thought."""
    events = [
        {"type": "message_start", "message": {"usage": {"input_tokens": 5}}},
        {"type": "message_stop"},
    ]
    thought, tokens = build_thought_from_events(events)
    assert thought.text is None
    assert thought.tool_calls == []
    assert tokens == 5


def test_build_thought_tool_with_empty_input():
    """Verify tool call with no input args."""
    events = [
        {"type": "message_start", "message": {"usage": {"input_tokens": 30}}},
        {"type": "content_block_start", "index": 0, "content_block": {
            "type": "tool_use", "id": "tool_789", "name": "list_files"
        }},
        {"type": "content_block_stop", "index": 0},
        {"type": "message_stop"},
    ]
    thought, _ = build_thought_from_events(events)
    assert len(thought.tool_calls) == 1
    assert thought.tool_calls[0].name == "list_files"
    assert thought.tool_calls[0].args == {}
