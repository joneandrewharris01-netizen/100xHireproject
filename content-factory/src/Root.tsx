import React from "react";
import { Composition } from "remotion";
import { WealthVideo } from "./compositions/WealthVideo";
import { AppsVideo } from "./compositions/AppsVideo";
import { FinanceVideo } from "./compositions/FinanceVideo";
import { CustomVideo } from "./compositions/CustomVideo";
import { ThreeDVideo } from "./compositions/ThreeDVideo";
import type { ContentData } from "./types/content";
import { getTotalFrames } from "./utils/timing";
import todayData from "./data/today.json";

const data = todayData as unknown as ContentData;

const VIDEO = { width: 1080, height: 1920, fps: 30 };

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const WealthComp = WealthVideo as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const AppsComp = AppsVideo as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const FinanceComp = FinanceVideo as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomComp = CustomVideo as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const ThreeDComp = ThreeDVideo as any;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="WealthVideo"
        component={WealthComp}
        durationInFrames={getTotalFrames(data.audio.durationSeconds)}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
        defaultProps={{ data }}
      />
      <Composition
        id="AppsVideo"
        component={AppsComp}
        durationInFrames={getTotalFrames(data.audio.durationSeconds)}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
        defaultProps={{ data }}
      />
      <Composition
        id="FinanceVideo"
        component={FinanceComp}
        durationInFrames={getTotalFrames(data.audio.durationSeconds)}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
        defaultProps={{ data }}
      />
      <Composition
        id="CustomVideo"
        component={CustomComp}
        durationInFrames={getTotalFrames(data.audio.durationSeconds)}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
        defaultProps={{ data }}
      />
      <Composition
        id="ThreeDVideo"
        component={ThreeDComp}
        durationInFrames={getTotalFrames(data.audio.durationSeconds)}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
        defaultProps={{ data }}
      />
    </>
  );
};
