"use client";

interface AudioSlidersProps {
  rate: string;
  pitch: string;
  onRateChange: (rate: string) => void;
  onPitchChange: (pitch: string) => void;
  accent?: string;
}

function parseRate(val: string): number {
  return parseInt(val.replace("%", "").replace("+", ""), 10) || 0;
}

function parsePitch(val: string): number {
  return parseInt(val.replace("Hz", "").replace("+", ""), 10) || 0;
}

export function AudioSliders({
  rate,
  pitch,
  onRateChange,
  onPitchChange,
  accent = "#00D4FF",
}: AudioSlidersProps) {
  const rateNum = parseRate(rate);
  const pitchNum = parsePitch(pitch);

  return (
    <div className="space-y-4">
      {/* Rate slider */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs text-gray-500 uppercase tracking-wider">Rate</label>
          <span className="text-xs font-mono" style={{ color: accent }}>
            {rateNum >= 0 ? "+" : ""}{rateNum}%
          </span>
        </div>
        <input
          type="range"
          min={-50}
          max={50}
          value={rateNum}
          onChange={(e) => {
            const v = parseInt(e.target.value);
            onRateChange(`${v >= 0 ? "+" : ""}${v}%`);
          }}
          className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
          style={{
            background: `linear-gradient(to right, ${accent}40, ${accent})`,
            accentColor: accent,
          }}
        />
        <div className="flex justify-between text-xs text-gray-600 mt-0.5">
          <span>-50%</span>
          <span>0</span>
          <span>+50%</span>
        </div>
      </div>

      {/* Pitch slider */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs text-gray-500 uppercase tracking-wider">Pitch</label>
          <span className="text-xs font-mono" style={{ color: accent }}>
            {pitchNum >= 0 ? "+" : ""}{pitchNum}Hz
          </span>
        </div>
        <input
          type="range"
          min={-10}
          max={10}
          value={pitchNum}
          onChange={(e) => {
            const v = parseInt(e.target.value);
            onPitchChange(`${v >= 0 ? "+" : ""}${v}Hz`);
          }}
          className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
          style={{
            background: `linear-gradient(to right, ${accent}40, ${accent})`,
            accentColor: accent,
          }}
        />
        <div className="flex justify-between text-xs text-gray-600 mt-0.5">
          <span>-10Hz</span>
          <span>0</span>
          <span>+10Hz</span>
        </div>
      </div>
    </div>
  );
}
