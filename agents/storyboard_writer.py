import os
import json
from groq import Groq
from pathlib import Path
from state.schema import PipelineState, Storyboard
from rag.retriever import retrieve_style_context

PROMPT = """You are a video editor. Given image analyses and a VideoIntent, produce a storyboard.
Rules:
- Select the BEST images (not all). Prioritize quality_score and mood alignment.
- Create a narrative arc: opening -> build -> climax -> close.
- Each scene must include: scene_index, image_path, duration_seconds, caption, transition, animation.
- image_path must be ONLY the filename like "AHD_6008.jpg" — no folder prefix.
- Caption tone must match the intent caption_tone.
- Timing must match pacing (slow=4-6s, moderate=2-4s, fast=1-2s).
Return ONLY a valid JSON object with keys: title, total_duration_seconds, scenes, narrative_arc.
IMPORTANT: narrative_arc must be a single string like "opening -> build -> climax -> close"
No markdown, no backticks."""

def write_storyboard(state: PipelineState) -> PipelineState:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    style_context = retrieve_style_context(state["intent"].visual_style)

    # Pass only filenames to the LLM
    analyses_clean = []
    for a in state['image_analyses']:
        d = a.model_dump()
        d['path'] = Path(d['path']).name  # strip folder
        analyses_clean.append(d)

    prompt = f"""{PROMPT}

Style context: {style_context}
VideoIntent: {state['intent'].model_dump_json(indent=2)}
Image analyses: {json.dumps(analyses_clean, indent=2)}

Generate the storyboard JSON now."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.choices[0].message.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    data = json.loads(raw)
    if isinstance(data.get("narrative_arc"), list):
        data["narrative_arc"] = " -> ".join(data["narrative_arc"])
    # Ensure image_path is just filename
    for scene in data.get("scenes", []):
        scene["image_path"] = Path(scene["image_path"]).name
    storyboard = Storyboard.model_validate(data)
    return {**state, "storyboard": storyboard}
