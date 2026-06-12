import { AbsoluteFill, Img, Sequence, interpolate, useCurrentFrame } from 'remotion'
import { staticFile } from 'remotion';

interface Scene {
  scene_index: number;
  image_path: string;
  duration_seconds: number;
  caption: string;
  transition: string;
  animation: string;
}

const scenes: Scene[] = [
  {
    scene_index: 1,
    image_path: "AHD_6008.jpg",
    duration_seconds: 6.0,
    caption: "Forever begins",
    transition: "cross-dissolve",
    animation: "fade-in"
  },
  {
    scene_index: 2,
    image_path: "DSC_6607.jpg",
    duration_seconds: 6.0,
    caption: "Promises made",
    transition: "cross-dissolve",
    animation: "fade-in"
  },
  {
    scene_index: 3,
    image_path: "_ASL9923.jpg",
    duration_seconds: 6.0,
    caption: "Love shines bright",
    transition: "cross-dissolve",
    animation: "fade-in"
  },
  {
    scene_index: 4,
    image_path: "AHD_6202.jpg",
    duration_seconds: 6.0,
    caption: "Together forever",
    transition: "cross-dissolve",
    animation: "fade-in"
  }
];

const fps = 30;

export const Main: React.FC = () => {
  return (
    <AbsoluteFill>
      {scenes.map((scene, index) => (
        <Sequence
          key={index}
          from={index * scene.duration_seconds * fps}
          durationInFrames={scene.duration_seconds * fps}
        >
          <Img
            src={staticFile(scene.image_path)}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              width: '100%',
              padding: 20,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              color: 'white',
              fontFamily: 'sans-serif',
              fontSize: 24,
            }}
          >
            {scene.caption}
          </div>
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

export default Main;