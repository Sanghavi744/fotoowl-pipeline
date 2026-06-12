import re
import subprocess
from pathlib import Path
from state.schema import PipelineState

SCRIPT_PATH = Path("./remotion_project/src/Composition.tsx")
PUBLIC_DIR = Path("./remotion_project/public").absolute()

def compile_and_fix(state: PipelineState) -> PipelineState:
    SCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    script = state["remotion_script"]

    # Clean markdown fences
    script = script.strip()
    for prefix in ["```tsx", "```typescript", "```ts", "```"]:
        if script.startswith(prefix):
            script = script[len(prefix):]
    script = script.rstrip("```").strip()

    # Fix missing first character
    if script.startswith("mport"):
        script = "i" + script

    # Replace any image src with absolute path to public folder
    def fix_image_src(match):
        full_path = match.group(1)
        filename = Path(full_path).name
        abs_path = str(PUBLIC_DIR / filename)
        return f'src="{abs_path}"'

    script = re.sub(r'src="([^"]+\.(jpg|jpeg|png|JPG|PNG))"', fix_image_src, script)

    SCRIPT_PATH.write_text(script)
    print(f"[Compiler] Script written. First line: {script.splitlines()[0]}")

    result = subprocess.run(
        ["npx", "remotion", "bundle", "./src/index.ts", "--log=error"],
        capture_output=True,
        text=True,
        cwd="./remotion_project",
        timeout=60,
    )

    if result.returncode == 0:
        print("[Compiler] Success!")
        return {**state, "compile_errors": [], "final_video_path": "__READY__"}

    errors = [l for l in result.stderr.strip().splitlines() if l.strip()][:5]
    print(f"[Compiler] Errors: {errors}")

    new_retry_count = state["retry_count"] + 1
    if new_retry_count >= state["max_retries"]:
        return {
            **state,
            "compile_errors": errors,
            "retry_count": new_retry_count,
            "final_video_path": "__READY__",
            "failure_report": f"Compiled with errors: {errors}",
        }

    return {**state, "compile_errors": errors, "retry_count": new_retry_count}
