import argparse
from pathlib import Path
from pipeline import build_graph
from state.schema import PipelineState

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()

    exts = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.PNG", "*.JPEG"]
    image_paths = sorted(p for ext in exts for p in Path(args.images).glob(ext))
    assert image_paths, f"No images found in {args.images}"

    initial_state: PipelineState = {
        "image_paths": [str(p) for p in image_paths],
        "user_prompt": args.prompt,
        "intent": None,
        "image_analyses": [],
        "storyboard": None,
        "remotion_script": None,
        "compile_errors": [],
        "retry_count": 0,
        "max_retries": args.max_retries,
        "final_video_path": None,
        "failure_report": None,
    }

    graph = build_graph()
    result = graph.invoke(initial_state, config={"recursion_limit": 50})

    if result["final_video_path"] and result["final_video_path"] != "__READY__":
        print(f"\n✅ Video rendered: {result['final_video_path']}")
    elif result["final_video_path"] == "__READY__":
        print(f"\n✅ Script compiled successfully!")
        print(f"Remotion script saved to: ./remotion_project/src/Composition.tsx")
    else:
        print(f"\n❌ Pipeline failed:\n{result['failure_report']}")

if __name__ == "__main__":
    main()
