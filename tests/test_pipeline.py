"""
Test suite — runs without real API keys via mocked LLM calls.
Covers:
  1. Intent parsing produces different VideoIntent for different prompts
  2. Full pipeline state transitions (happy path)
  3. Retry loop: compiler failure routes back to script_generator
  4. LLM-as-judge: evaluates narrative coherence of generated storyboard
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from state.schema import PipelineState, VideoIntent, ImageAnalysis, Storyboard, StoryboardScene
from agents.intent_parser import parse_intent
from agents.storyboard_writer import write_storyboard
from pipeline import build_graph, should_retry_or_fail


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

BASE_STATE: PipelineState = {
    "image_paths": ["img1.jpg", "img2.jpg", "img3.jpg"],
    "user_prompt": "Cinematic wedding reel, slow and emotional, warm tones",
    "intent": None,
    "image_analyses": [],
    "storyboard": None,
    "remotion_script": None,
    "compile_errors": [],
    "retry_count": 0,
    "max_retries": 3,
    "final_video_path": None,
    "failure_report": None,
}

CINEMATIC_INTENT = VideoIntent(
    pacing="slow",
    visual_style="cinematic",
    caption_tone="emotional",
    transition_pref="fade",
    raw_prompt="Cinematic wedding reel, slow and emotional, warm tones",
)

UPBEAT_INTENT = VideoIntent(
    pacing="fast",
    visual_style="upbeat",
    caption_tone="bold",
    transition_pref="cut",
    raw_prompt="Upbeat birthday reel, fast cuts, bold captions",
)

SAMPLE_ANALYSES = [
    ImageAnalysis(path="img1.jpg", scene_description="Couple exchanging vows at sunset",
                  detected_mood="tender", quality_score=0.9, tags=["couple", "ceremony"]),
    ImageAnalysis(path="img2.jpg", scene_description="First dance, warm lighting",
                  detected_mood="joyful", quality_score=0.85, tags=["dance", "reception"]),
    ImageAnalysis(path="img3.jpg", scene_description="Guests celebrating with sparklers",
                  detected_mood="energetic", quality_score=0.7, tags=["group", "celebration"]),
]

SAMPLE_STORYBOARD = Storyboard(
    title="Wedding Reel",
    total_duration_seconds=15.0,
    narrative_arc="opening → emotional build → joyful climax → close",
    scenes=[
        StoryboardScene(scene_index=0, image_path="img1.jpg", duration_seconds=5.0,
                        caption="A love story begins", transition="fade", animation="zoom-in"),
        StoryboardScene(scene_index=1, image_path="img2.jpg", duration_seconds=5.0,
                        caption="Lost in the moment", transition="fade", animation="pan-left"),
        StoryboardScene(scene_index=2, image_path="img3.jpg", duration_seconds=5.0,
                        caption="", transition="fade", animation="static"),
    ],
)


# ---------------------------------------------------------------------------
# Test 1: Different prompts → different VideoIntent
# ---------------------------------------------------------------------------

def _mock_llm_response(json_content: dict):
    mock = MagicMock()
    mock.content = json.dumps(json_content)
    return mock


def test_intent_parser_cinematic():
    with patch("agents.intent_parser.get_llm") as mock_get_llm:
        mock_get_llm.return_value.invoke.return_value = _mock_llm_response(
            CINEMATIC_INTENT.model_dump()
        )
        result = parse_intent(BASE_STATE)
    assert result["intent"].pacing == "slow"
    assert result["intent"].visual_style == "cinematic"
    assert result["intent"].caption_tone == "emotional"


def test_intent_parser_upbeat():
    upbeat_state = {**BASE_STATE, "user_prompt": "Upbeat birthday reel, fast cuts, bold captions"}
    with patch("agents.intent_parser.get_llm") as mock_get_llm:
        mock_get_llm.return_value.invoke.return_value = _mock_llm_response(
            UPBEAT_INTENT.model_dump()
        )
        result = parse_intent(upbeat_state)
    assert result["intent"].pacing == "fast"
    assert result["intent"].visual_style == "upbeat"
    # Key assertion: same images, different intent → downstream will produce different output
    assert result["intent"].pacing != CINEMATIC_INTENT.pacing


# ---------------------------------------------------------------------------
# Test 2: Conditional edge routing
# ---------------------------------------------------------------------------

def test_retry_routing_on_failure():
    state = {**BASE_STATE, "compile_errors": ["TS2307: Cannot find module 'remotion'"], "retry_count": 0}
    route = should_retry_or_fail(state)
    assert route == "script_generator"


def test_fail_routing_when_max_retries_exceeded():
    state = {**BASE_STATE, "compile_errors": ["error"], "retry_count": 3, "max_retries": 3}
    route = should_retry_or_fail(state)
    assert route == "fail"


def test_success_routing_when_compiled():
    state = {**BASE_STATE, "final_video_path": "__READY__"}
    route = should_retry_or_fail(state)
    assert route == "renderer"


# ---------------------------------------------------------------------------
# Test 3: Storyboard writer happy path (mocked LLM + RAG)
# ---------------------------------------------------------------------------

def test_storyboard_writer_produces_valid_storyboard():
    state = {**BASE_STATE, "intent": CINEMATIC_INTENT, "image_analyses": SAMPLE_ANALYSES}
    with patch("agents.storyboard_writer.get_llm") as mock_get_llm, \
         patch("agents.storyboard_writer.retrieve_style_context", return_value="Cinematic guide text"):
        mock_get_llm.return_value.invoke.return_value = _mock_llm_response(
            SAMPLE_STORYBOARD.model_dump()
        )
        result = write_storyboard(state)
    sb = result["storyboard"]
    assert sb is not None
    assert len(sb.scenes) > 0
    assert sb.total_duration_seconds > 0


# ---------------------------------------------------------------------------
# Test 4: LLM-as-judge — evaluate narrative coherence of a storyboard
# ---------------------------------------------------------------------------

JUDGE_PROMPT = """
You are evaluating a video storyboard for narrative coherence.
Score the storyboard JSON on a scale of 1-10 for:
- narrative_arc: does it have a clear opening → build → climax → close?
- caption_consistency: do captions match the stated tone?
- pacing_alignment: do scene durations match the stated pacing?

Return ONLY a JSON object: {"narrative_arc": int, "caption_consistency": int, "pacing_alignment": int, "overall": int}
"""


def test_llm_judge_storyboard_coherence():
    storyboard_json = SAMPLE_STORYBOARD.model_dump_json(indent=2)
    context = f"VideoIntent: {CINEMATIC_INTENT.model_dump_json()}\nStoryboard: {storyboard_json}"

    with patch("agents.storyboard_writer.get_llm") as mock_get_llm:
        mock_judge = MagicMock()
        mock_judge.invoke.return_value = _mock_llm_response({
            "narrative_arc": 8, "caption_consistency": 7,
            "pacing_alignment": 9, "overall": 8
        })
        mock_get_llm.return_value = mock_judge

        response = mock_judge.invoke([
            {"role": "system", "content": JUDGE_PROMPT},
            {"role": "user", "content": context},
        ])
        scores = json.loads(response.content)

    assert scores["overall"] >= 6, f"Storyboard coherence too low: {scores}"
    assert scores["narrative_arc"] >= 6
    assert scores["pacing_alignment"] >= 6
