import os
from groq import Groq
from state.schema import PipelineState, ImageAnalysis
from pathlib import Path

PROMPT = """You are analysing a wedding photo filename for a video editor.
Based on the filename, return a JSON object with ONLY these keys:
- scene_description: 1-2 sentence description (assume it's a professional Indian wedding photo)
- detected_mood: single word (joyful, tender, dramatic, calm, energetic)
- quality_score: float 0.85-0.95
- tags: list of 3-5 relevant tags like ["bride", "ceremony", "portrait", "couple", "celebration"]

Return ONLY the raw JSON object. No markdown, no backticks."""

def analyse_images(state: PipelineState) -> PipelineState:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    analyses = []
    for img_path in state["image_paths"]:
        filename = Path(img_path).name
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"{PROMPT}\n\nFilename: {filename}"}],
        )
        raw = response.choices[0].message.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        import json
        data = json.loads(raw)
        data["path"] = img_path
        analysis = ImageAnalysis.model_validate(data)
        analyses.append(analysis)
    return {**state, "image_analyses": analyses}
