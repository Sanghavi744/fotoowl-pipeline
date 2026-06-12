import os
import json
from groq import Groq
from state.schema import PipelineState, VideoIntent

PROMPT = """Parse this video creative brief into a JSON object with these exact keys:
- pacing: one of "slow", "moderate", "fast"
- visual_style: one of "cinematic", "upbeat", "corporate", "romantic", "documentary"
- caption_tone: one of "emotional", "bold", "minimal", "professional", "playful"
- transition_pref: one of "fade", "cut", "slide", "none"
- raw_prompt: the original prompt verbatim

Return ONLY the JSON object. No markdown, no backticks."""

def parse_intent(state: PipelineState) -> PipelineState:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"{PROMPT}\n\nPrompt: {state['user_prompt']}"}],
    )
    raw = response.choices[0].message.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    intent = VideoIntent.model_validate_json(raw)
    return {**state, "intent": intent}
