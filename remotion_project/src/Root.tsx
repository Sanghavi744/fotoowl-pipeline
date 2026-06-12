import { Composition } from 'remotion';
import { Main } from './Composition';

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
