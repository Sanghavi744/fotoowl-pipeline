from typing import Optional
from typing_extensions import TypedDict
from pydantic import BaseModel


class VideoIntent(BaseModel):
    pacing: str
    visual_style: str
    caption_tone: str
    transition_pref: str
    raw_prompt: str


class ImageAnalysis(BaseModel):
    path: str
    scene_description: str
    detected_mood: str
    quality_score: float
    tags: list[str]


class StoryboardScene(BaseModel):
    scene_index: int
    image_path: str
    duration_seconds: float
    caption: str
    transition: str
    animation: str


class Storyboard(BaseModel):
    title: str
    total_duration_seconds: float
    scenes: list[StoryboardScene]
    narrative_arc: str


class PipelineState(TypedDict):
    image_paths: list[str]
    user_prompt: str
    intent: Optional[VideoIntent]
    image_analyses: list[ImageAnalysis]
    storyboard: Optional[Storyboard]
    remotion_script: Optional[str]
    compile_errors: list[str]
    retry_count: int
    max_retries: int
    final_video_path: Optional[str]
    failure_report: Optional[str]
