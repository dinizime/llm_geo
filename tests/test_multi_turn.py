"""Unit tests for multi-turn conversation, GeometryStore, and session management.

These tests mock the LLM client — no network, no API key required.
Run with: pytest tests/test_multi_turn.py -v
"""

import json
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from llm_tool_calling.agent import SYSTEM_PROMPT, AgentResult, run_agent
from llm_tool_calling.geometry_store import GeometryStore


# ═══════════════════════════════════════════════════════════════
# Helpers: fake OpenAI responses
# ═══════════════════════════════════════════════════════════════


def _make_tool_call(call_id, name, arguments):
    tc = SimpleNamespace()
    tc.id = call_id
    tc.type = "function"
    tc.function = SimpleNamespace()
    tc.function.name = name
    tc.function.arguments = json.dumps(arguments)
    return tc


def _make_response(content="resposta", tool_calls=None, finish_reason="stop",
                   prompt_tokens=10, completion_tokens=5):
    choice = SimpleNamespace()
    choice.finish_reason = finish_reason
    choice.message = SimpleNamespace()
    choice.message.content = content
    choice.message.tool_calls = tool_calls
    usage = SimpleNamespace()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    resp = SimpleNamespace()
    resp.choices = [choice]
    resp.usage = usage
    return resp


def _make_client(*responses):
    """Create a mock OpenAI client that returns responses in sequence."""
    client = MagicMock()
    client.chat.completions.create.side_effect = list(responses)
    return client


def _make_provider_config():
    pc = SimpleNamespace()
    pc.extra_body = None
    return pc


# ═══════════════════════════════════════════════════════════════
# GeometryStore tests
# ═══════════════════════════════════════════════════════════════


class TestGeometryStore:
    def test_put_get_roundtrip(self):
        gs = GeometryStore()
        geojson = {"type": "Point", "coordinates": [-53.81, -29.68]}
        ref = gs.put(geojson, "test")
        assert gs.get(ref) == geojson

    def test_get_missing_raises(self):
        gs = GeometryStore()
        with pytest.raises(KeyError, match="not found"):
            gs.get("geom_nonexistent")

    def test_refs_unique(self):
        gs = GeometryStore()
        geojson = {"type": "Point", "coordinates": [0, 0]}
        ref1 = gs.put(geojson)
        ref2 = gs.put(geojson)
        assert ref1 != ref2

    def test_summary(self):
        gs = GeometryStore()
        geojson = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        ref = gs.put(geojson, "meu_poligono")
        s = gs.summary(ref)
        assert s["geometry_ref"] == ref
        assert s["type"] == "Polygon"
        assert s["label"] == "meu_poligono"

    def test_clear(self):
        gs = GeometryStore()
        ref = gs.put({"type": "Point", "coordinates": [0, 0]})
        gs.clear()
        assert len(gs) == 0
        with pytest.raises(KeyError):
            gs.get(ref)

    def test_len(self):
        gs = GeometryStore()
        assert len(gs) == 0
        gs.put({"type": "Point", "coordinates": [0, 0]})
        assert len(gs) == 1
        gs.put({"type": "Point", "coordinates": [1, 1]})
        assert len(gs) == 2


# ═══════════════════════════════════════════════════════════════
# Agent multi-turn tests (mocked LLM)
# ═══════════════════════════════════════════════════════════════


class TestAgentMultiTurn:
    def test_first_turn_has_system_prompt(self):
        """Turn 1 without messages_history starts with system prompt."""
        client = _make_client(_make_response("Olá!"))
        result = run_agent("Oi", client=client, model="test", provider_config=_make_provider_config())

        call_args = client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == SYSTEM_PROMPT
        assert messages[1] == {"role": "user", "content": "Oi"}

    def test_final_assistant_message_in_history(self):
        """result._messages ends with the final assistant message."""
        client = _make_client(_make_response("Aqui está a resposta."))
        result = run_agent("Pergunta", client=client, model="test", provider_config=_make_provider_config())

        assert result.error is None
        assert result._messages[-1]["role"] == "assistant"
        assert result._messages[-1]["content"] == "Aqui está a resposta."

    def test_second_turn_preserves_history(self):
        """Turn 2 with messages_history contains full history + new query."""
        # Turn 1
        client1 = _make_client(_make_response("Resposta 1"))
        r1 = run_agent("Pergunta 1", client=client1, model="test", provider_config=_make_provider_config())

        # Turn 2
        client2 = _make_client(_make_response("Resposta 2"))
        r2 = run_agent(
            "Pergunta 2", client=client2, model="test",
            provider_config=_make_provider_config(),
            messages_history=r1._messages,
            geometry_store=r1._geometry_store,
        )

        call_args = client2.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        # Should have: system, user1, assistant1, user2
        assert messages[0]["role"] == "system"
        assert messages[1]["content"] == "Pergunta 1"
        assert messages[2] == {"role": "assistant", "content": "Resposta 1"}
        assert messages[3] == {"role": "user", "content": "Pergunta 2"}

    def test_messages_history_not_mutated(self):
        """Original messages_history list is not modified by run_agent."""
        client1 = _make_client(_make_response("R1"))
        r1 = run_agent("Q1", client=client1, model="test", provider_config=_make_provider_config())

        original_history = list(r1._messages)
        original_len = len(original_history)

        client2 = _make_client(_make_response("R2"))
        run_agent(
            "Q2", client=client2, model="test",
            provider_config=_make_provider_config(),
            messages_history=r1._messages,
        )

        # r1._messages should not have been mutated
        assert len(r1._messages) == original_len

    def test_multi_turn_with_tool_calls(self):
        """Turn 1 calls a tool; turn 2 sees tool_call + result in history."""
        # Turn 1: LLM calls geocode, then gives final answer
        tool_call = _make_tool_call("tc_1", "geocode", {"place_name": "Alegrete"})
        resp_with_tools = _make_response(
            content="Vou geocodificar.",
            tool_calls=[tool_call],
            finish_reason="tool_calls",
        )
        resp_final = _make_response("Alegrete fica no RS.")
        client1 = _make_client(resp_with_tools, resp_final)

        gs = GeometryStore()
        # We need to mock tool_handlers.dispatch to return a valid result
        with patch("llm_tool_calling.agent.ToolHandlers") as MockHandlers:
            instance = MockHandlers.return_value
            instance.dispatch.return_value = {
                "lat": -29.78,
                "lon": -55.79,
                "display_name": "Alegrete, RS",
            }
            r1 = run_agent("Onde fica Alegrete?", client=client1, model="test",
                           provider_config=_make_provider_config(), geometry_store=gs)

        assert r1.error is None
        assert len(r1.trace) == 1
        assert r1.trace[0]["tool"] == "geocode"

        # Turn 2: check r2._messages contains full history from both turns
        client2 = _make_client(_make_response("Resposta do turno 2"))
        r2 = run_agent(
            "E Uruguaiana?", client=client2, model="test",
            provider_config=_make_provider_config(),
            messages_history=r1._messages,
            geometry_store=r1._geometry_store,
        )

        msgs = r2._messages
        roles = [m["role"] for m in msgs]

        # Should contain tool interactions from turn 1
        assert "tool" in roles, f"Expected tool message in history. Got roles: {roles}"
        # Last message is turn 2's final assistant response
        assert msgs[-1] == {"role": "assistant", "content": "Resposta do turno 2"}
        # Turn 2 user message should be present
        user_msgs = [m for m in msgs if m["role"] == "user"]
        assert any(m["content"] == "E Uruguaiana?" for m in user_msgs)
        # Tool result from turn 1 present
        tool_msgs = [m for m in msgs if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        assert tool_msgs[0]["tool_call_id"] == "tc_1"
        # At least 3 assistant messages: tool_calls, final turn 1, final turn 2
        assert roles.count("assistant") >= 3

    def test_geometry_store_shared_across_turns(self):
        """Geometry refs from turn 1 remain accessible in turn 2."""
        gs = GeometryStore()
        ref = gs.put({"type": "Point", "coordinates": [-55.79, -29.78]}, "Alegrete")

        # Turn 1
        client1 = _make_client(_make_response("Turno 1"))
        r1 = run_agent("Q1", client=client1, model="test",
                       provider_config=_make_provider_config(), geometry_store=gs)

        # Turn 2 reuses the same geometry_store
        assert r1._geometry_store.get(ref) == {"type": "Point", "coordinates": [-55.79, -29.78]}

        client2 = _make_client(_make_response("Turno 2"))
        r2 = run_agent("Q2", client=client2, model="test",
                       provider_config=_make_provider_config(),
                       messages_history=r1._messages,
                       geometry_store=r1._geometry_store)

        # Still accessible
        assert r2._geometry_store.get(ref) == {"type": "Point", "coordinates": [-55.79, -29.78]}

    def test_agent_result_fields(self):
        """AgentResult has correct metrics after a simple turn."""
        client = _make_client(_make_response("OK", prompt_tokens=100, completion_tokens=20))
        r = run_agent("Teste", client=client, model="test", provider_config=_make_provider_config())

        assert r.answer == "OK"
        assert r.error is None
        assert r.iterations == 1
        assert r.prompt_tokens == 100
        assert r.completion_tokens == 20
        assert r.total_tokens == 120
        assert r.duration_ms >= 0
        assert r.trace == []


# ═══════════════════════════════════════════════════════════════
# Session management tests (Flask test client)
# ═══════════════════════════════════════════════════════════════


class TestSessionManagement:
    """Tests for web.py session store using Flask test client + mocked agent."""

    @pytest.fixture
    def client(self):
        """Flask test client with mocked run_agent."""
        with patch("llm_tool_calling.web.run_agent") as mock_agent:
            # Default: return a simple AgentResult
            mock_agent.side_effect = self._make_agent_side_effect()
            from llm_tool_calling.web import app, _sessions
            _sessions.clear()
            app.config["TESTING"] = True
            with app.test_client() as c:
                self._mock_agent = mock_agent
                self._sessions = _sessions
                yield c

    def _make_agent_side_effect(self):
        """Returns a side_effect function that creates proper AgentResults."""
        def side_effect(query, **kwargs):
            gs = kwargs.get("geometry_store") or GeometryStore()
            history = kwargs.get("messages_history")
            if history is not None:
                msgs = list(history)
                msgs.append({"role": "user", "content": query})
            else:
                msgs = [
                    {"role": "system", "content": "system"},
                    {"role": "user", "content": query},
                ]
            msgs.append({"role": "assistant", "content": f"Resposta para: {query}"})
            return AgentResult(
                answer=f"Resposta para: {query}",
                trace=[],
                iterations=1,
                duration_ms=100,
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
                _geometry_store=gs,
                _messages=msgs,
            )
        return side_effect

    def _post_stream_and_get_final(self, client, query, session_id=None):
        """POST to search-stream and extract the final SSE event."""
        payload = {"query": query}
        if session_id:
            payload["session_id"] = session_id
        resp = client.post("/api/search-stream",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code == 200

        final = None
        for line in resp.data.decode("utf-8").split("\n"):
            if line.startswith("data: "):
                event = json.loads(line[6:])
                if event.get("type") == "final":
                    final = event
        return final

    def test_first_request_creates_session(self, client):
        final = self._post_stream_and_get_final(client, "Olá")
        assert final is not None
        assert "session_id" in final
        assert final["session_id"] in self._sessions

    def test_second_request_reuses_session(self, client):
        final1 = self._post_stream_and_get_final(client, "Pergunta 1")
        sid = final1["session_id"]

        final2 = self._post_stream_and_get_final(client, "Pergunta 2", session_id=sid)
        assert final2["session_id"] == sid

        # Verify run_agent was called with messages_history on second call
        calls = self._mock_agent.call_args_list
        assert len(calls) == 2
        second_call_kwargs = calls[1].kwargs
        assert second_call_kwargs["messages_history"] is not None

    def test_invalid_session_creates_new(self, client):
        final = self._post_stream_and_get_final(client, "Olá", session_id="invalid_id")
        assert final is not None
        assert final["session_id"] != "invalid_id"
        assert final["session_id"] in self._sessions

    def test_clear_session(self, client):
        final = self._post_stream_and_get_final(client, "Olá")
        sid = final["session_id"]
        assert sid in self._sessions

        resp = client.post("/api/clear-session",
                           data=json.dumps({"session_id": sid}),
                           content_type="application/json")
        assert resp.status_code == 200
        assert sid not in self._sessions

    def test_session_cleanup_ttl(self, client):
        final = self._post_stream_and_get_final(client, "Olá")
        sid = final["session_id"]

        # Manually expire the session
        from llm_tool_calling.web import _SESSION_TTL
        self._sessions[sid]["last_access"] = time.time() - _SESSION_TTL - 1

        # Next request triggers cleanup
        final2 = self._post_stream_and_get_final(client, "Outra pergunta")
        assert sid not in self._sessions
        assert final2["session_id"] != sid
