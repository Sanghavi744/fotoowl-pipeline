import os
import json
import time
from groq import Groq
from state.schema import PipelineState
from rag.retriever import retrieve_api_context, retrieve_error_fix

PROMPT = """You are a Remotion expert. Generate a valid TypeScript/TSX file.
IMPORTANT: Start the file DIRECTLY with: import { ... } from 'remotion';
No text before the import statement.

Requirements:
- First line must be: import { AbsoluteFill, Img, Sequence, interpolate, useCurrentFrame } from 'remotion';
- Export a Main component as: export const Main: React.FC = () => {
- Each scene uses Sequence with durationInFrames at 30fps
- Add caption overlay using a styled div
- End with: export default Main;

Return ONLY the TypeScript code starting with the import statement."""

def generate_script(state: PipelineState) -> PipelineState:
    time.sleep(5)
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    is_retry = state["retry_count"] > 0
    errors = state.get("compile_errors", [])

    prompt = f"""{PROMPT}

Storyboard: {json.dumps(state['storyboard'].model_dump(), indent=2)}
VideoIntent: {state['intent'].model_dump_json(indent=2)}

Remember: Start DIRECTLY with the import line, nothing before it."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
    )
    raw = response.choices[0].message.content

    # Find first import line
    lines = raw.split('\n')
    start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('import'):
            start = i
            break

    script = '\n'.join(lines[start:]).strip().rstrip("```").strip()

    # Fix missing first character
    if script.startswith('mport'):
        script = 'i' + script

    return {
        **state,
        "remotion_script": script,
        "retry_count": state["retry_count"] + (1 if is_retry else 0),
    }
