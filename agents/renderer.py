import subprocess
from pathlib import Path
from state.schema import PipelineState

OUTPUT_PATH = Path("./sample_output/output.mp4")

def render_video(state: PipelineState) -> PipelineState:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "npx", "remotion", "render",
            "./src/index.ts",        # entry point
            "Composition",
            str(OUTPUT_PATH.absolute()),
            "--log=error",
        ],
        capture_output=True,
        text=True,
        cwd="./remotion_project",
    )

    if result.returncode == 0:
        print(f"[Renderer] Video rendered: {OUTPUT_PATH}")
        return {**state, "final_video_path": str(OUTPUT_PATH)}

    print(f"[Renderer] Error: {result.stderr[:200]}")
    failure = f"Render failed:\n{result.stderr.strip()}"
    return {**state, "final_video_path": None, "failure_report": failure}
