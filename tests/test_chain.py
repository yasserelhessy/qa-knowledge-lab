import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from app.chain import Assistant, REFUSAL
from app.retrieval import retrieve


def test_extracts_cited_evidence(assistant):
    answer = assistant.invoke("What are release gates?")
    assert answer.answer == answer.sources[0].excerpt
    assert answer.status == "answered"


def test_empty_corpus_fails_closed():
    answer = Assistant(documents=[]).invoke("release gates")
    assert answer.status == "refused"
    assert answer.sources == []


def test_injected_fixture_is_isolated():
    docs = [{"id": "test-only", "title": "Fixture", "text": "Unique fixture evidence.", "keywords": "sandbox"}]
    assert Assistant(documents=docs).invoke("sandbox").sources[0].id == "test-only"
    assert Assistant().invoke("sandbox").status == "refused"


def test_retrieval_threshold():
    docs = [{"keywords": "one two three", "id": "x"}]
    assert retrieve("one two three four five", docs)["document"] is not None
    assert retrieve("one two three four five six", docs)["document"] is None


def test_optional_model_receives_prompt_and_is_parsed():
    seen = []
    def fake(prompt):
        seen.append(prompt.to_messages())
        return AIMessage(content="Model text")
    answer = Assistant("openai", model=RunnableLambda(fake)).invoke("release gates")
    assert answer.answer == "Model text"
    assert "API contract" in seen[0][0].content
    assert seen[0][1].content == "release gates"


def test_refused_retrieval_does_not_call_model():
    def unexpected(prompt):
        raise AssertionError("Model must not be invoked")
    answer = Assistant("openai", model=RunnableLambda(unexpected)).invoke("penguins")
    assert answer.status == "refused"


@pytest.mark.parametrize("output", [REFUSAL, "   "])
def test_model_refusal_has_no_citations(output):
    answer = Assistant("openai", model=RunnableLambda(lambda _: AIMessage(content=output))).invoke("release gates")
    assert answer.status == "refused"
    assert answer.sources == []


def test_invalid_mode():
    with pytest.raises(ValueError):
        Assistant("typo")
