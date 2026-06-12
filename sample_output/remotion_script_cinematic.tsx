import { AbsoluteFill, Img, Sequence, useCurrentFrame, interpolate } from 'remotion';

// ── Scene components ──────────────────────────────────────────────────────────

const ZoomIn: React.FC<{ src: string; caption: string; dur: number }> = ({ src, caption, dur }) => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, dur], [1, 1.12], { extrapolateRight: 'clamp' });
  const opacity = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ transform: `scale(${scale})` }}>
        <Img src={src} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      </AbsoluteFill>
      {caption && (
        <div style={{
          position: 'absolute', bottom: 90, width: '100%', textAlign: 'center',
          opacity, fontSize: 38, color: 'white', fontFamily: 'Georgia, serif',
          fontStyle: 'italic', textShadow: '0 2px 12px rgba(0,0,0,0.6)',
          letterSpacing: '0.04em',
        }}>
          {caption}
        </div>
      )}
    </AbsoluteFill>
  );
};

const PanLeft: React.FC<{ src: string; caption: string; dur: number }> = ({ src, caption, dur }) => {
  const frame = useCurrentFrame();
  const x = interpolate(frame, [0, dur], [0, -60], { extrapolateRight: 'clamp' });
  const opacity = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ transform: `translateX(${x}px)`, width: 'calc(100% + 60px)' }}>
        <Img src={src} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      </AbsoluteFill>
      {caption && (
        <div style={{
          position: 'absolute', bottom: 90, width: '100%', textAlign: 'center',
          opacity, fontSize: 38, color: 'white', fontFamily: 'Georgia, serif',
          fontStyle: 'italic', textShadow: '0 2px 12px rgba(0,0,0,0.6)',
        }}>
          {caption}
        </div>
      )}
    </AbsoluteFill>
  );
};

const Static: React.FC<{ src: string; caption: string }> = ({ src, caption }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill>
      <Img src={src} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      {caption && (
        <div style={{
          position: 'absolute', bottom: 90, width: '100%', textAlign: 'center',
          opacity, fontSize: 38, color: 'white', fontFamily: 'Georgia, serif',
          fontStyle: 'italic', textShadow: '0 2px 12px rgba(0,0,0,0.6)',
        }}>
          {caption}
        </div>
      )}
    </AbsoluteFill>
  );
};

// Fade overlay between scenes
const FadeOut: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [dur - 12, dur], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return <AbsoluteFill style={{ backgroundColor: 'black', opacity }} />;
};

// ── Main composition ──────────────────────────────────────────────────────────

const FPS = 30;
const scenes = [
  { file: 'AHD_6008.jpg',  caption: 'A love story begins', animation: 'zoom-in',  dur: 5 },
  { file: 'DSC_4491.jpg',  caption: 'Together, always',    animation: 'pan-left', dur: 5 },
  { file: 'DSC_6607.jpg',  caption: '',                    animation: 'static',   dur: 5 },
  { file: 'AHD_6202.jpg',  caption: 'Every detail, a memory', animation: 'zoom-in', dur: 4 },
  { file: '_ASL9923.jpg',  caption: '',                    animation: 'pan-left', dur: 5 },
];

export const Main: React.FC = () => {
  let offset = 0;
  return (
    <AbsoluteFill style={{ backgroundColor: 'black' }}>
      {scenes.map((s, i) => {
        const from = offset * FPS;
        const dur = s.dur * FPS;
        offset += s.dur;
        const src = `./public/${s.file}`;
        return (
          <Sequence key={i} from={from} durationInFrames={dur}>
            {s.animation === 'zoom-in'  && <ZoomIn  src={src} caption={s.caption} dur={dur} />}
            {s.animation === 'pan-left' && <PanLeft src={src} caption={s.caption} dur={dur} />}
            {s.animation === 'static'   && <Static  src={src} caption={s.caption} />}
            <FadeOut dur={dur} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
