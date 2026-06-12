"""
RAG Layer — Chroma vector store with two collections:
  1. style_guides   — visual treatment per style (cinematic, upbeat, corporate...)
  2. remotion_api   — Remotion component usage snippets

Chunking strategy:
  - Style entries: short documents (~150 words), kept as whole chunks.
    They describe a gestalt; splitting loses coherence.
  - Code snippets: kept as single self-contained examples (~30-80 lines).
    Splitting code mid-function breaks them. One snippet = one chunk.
"""
import chromadb
from chromadb.utils import embedding_functions

_client = chromadb.PersistentClient(path="./rag_store")
_ef = embedding_functions.DefaultEmbeddingFunction()  # local, no API key needed

_styles = _client.get_or_create_collection("style_guides",   embedding_function=_ef)
_api    = _client.get_or_create_collection("remotion_api",   embedding_function=_ef)


# ---------------------------------------------------------------------------
# Seed data — call once on first run
# ---------------------------------------------------------------------------

STYLE_DOCS = {
    "cinematic": """
Cinematic style: slow pacing (4-6s per scene), warm amber or desaturated tones.
Prefer cross-dissolve transitions. Captions appear with fade-in after 1s, minimal text.
Focus on emotional moments: close-ups, quiet scenes, wide establishing shots.
Narrative arc builds slowly. Music should be orchestral or ambient.
    """.strip(),

    "upbeat": """
Upbeat style: fast pacing (1-2s per scene), high saturation, bright tones.
Use hard cuts or flash transitions. Bold caption overlays, large font, contrasting colour.
Select high-energy images: group shots, dancing, laughing, action.
Quick zoom-ins and pan-cuts reinforce energy. Arc: immediate peak, sustained excitement.
    """.strip(),

    "corporate": """
Corporate style: moderate pacing (2-3s per scene), clean white or navy backgrounds.
Subtle slide or fade transitions. Professional caption tone, sentence case, small font.
Prefer images with clean backgrounds, presented individuals, product or venue shots.
Arc: context → highlights → close with logo or CTA.
    """.strip(),
}

API_DOCS = {
    "sequence_img_basic": """
// Basic Remotion scene: image fills screen for N frames
import { AbsoluteFill, Img, Sequence } from 'remotion';

export const Scene: React.FC<{ src: string; from: number; dur: number }> = ({ src, from, dur }) => (
  <Sequence from={from} durationInFrames={dur}>
    <AbsoluteFill>
      <Img src={src} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
    </AbsoluteFill>
  </Sequence>
);
    """.strip(),

    "interpolate_zoom": """
// Zoom-in animation using interpolate
import { useCurrentFrame, interpolate } from 'remotion';

const frame = useCurrentFrame();
const scale = interpolate(frame, [0, durationInFrames], [1, 1.15], {
  extrapolateLeft: 'clamp',
  extrapolateRight: 'clamp',
});
// Apply: style={{ transform: `scale(${scale})` }}
    """.strip(),

    "caption_overlay": """
// Caption overlay with fade-in
import { useCurrentFrame, interpolate } from 'remotion';

const opacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
// JSX:
// <div style={{ position: 'absolute', bottom: 80, width: '100%', textAlign: 'center',
//               opacity, fontSize: 32, color: 'white', textShadow: '0 2px 8px rgba(0,0,0,0.7)' }}>
//   {caption}
// </div>
    """.strip(),

    "root_composition": """
// Root.tsx — registers the composition
import { Composition } from 'remotion';
import { Main } from './Main';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Composition"
    component={Main}
    durationInFrames={300}
    fps={30}
    width={1920}
    height={1080}
  />
);
    """.strip(),
}


def seed_rag():
    """Seed both collections. Safe to call repeatedly (upsert by ID)."""
    _styles.upsert(
        ids=list(STYLE_DOCS.keys()),
        documents=list(STYLE_DOCS.values()),
    )
    _api.upsert(
        ids=list(API_DOCS.keys()),
        documents=list(API_DOCS.values()),
    )
    print("RAG seeded.")


# ---------------------------------------------------------------------------
# Retrieval helpers called by agents
# ---------------------------------------------------------------------------

def retrieve_style_context(visual_style: str, n_results: int = 2) -> str:
    results = _styles.query(query_texts=[visual_style], n_results=n_results)
    return "\n\n".join(results["documents"][0])


def retrieve_api_context(query: str, n_results: int = 3) -> str:
    results = _api.query(query_texts=[query], n_results=n_results)
    return "\n\n".join(results["documents"][0])


def retrieve_error_fix(error: str, n_results: int = 1) -> str:
    """Retrieve the API snippet most relevant to a compile error."""
    results = _api.query(query_texts=[error], n_results=n_results)
    return results["documents"][0][0] if results["documents"][0] else ""


if __name__ == "__main__":
    seed_rag()
