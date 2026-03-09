"use client";

interface AnimationPickerProps {
  value: string;
  onChange: (anim: string) => void;
  accent?: string;
}

const ANIMATIONS = [
  { id: "slamBottom", label: "Slam Bottom", preview: "Elements slam up from bottom" },
  { id: "slamTop", label: "Slam Top", preview: "Elements slam down from top" },
  { id: "slamLeft", label: "Slam Left", preview: "Elements slide in from left" },
  { id: "slamRight", label: "Slam Right", preview: "Elements slide in from right" },
  { id: "zoomCenter", label: "Zoom Center", preview: "Elements zoom in from center" },
  { id: "scaleUp", label: "Scale Up", preview: "Elements scale up smoothly" },
];

export function AnimationPicker({ value, onChange, accent = "#00D4FF" }: AnimationPickerProps) {
  return (
    <div>
      <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">
        Animation Style
      </label>
      <div className="grid grid-cols-3 gap-2">
        {ANIMATIONS.map((anim) => {
          const isActive = anim.id === value;
          return (
            <button
              key={anim.id}
              onClick={() => onChange(anim.id)}
              className={`p-2 rounded-lg border text-center transition-all ${
                isActive
                  ? ""
                  : "border-surface-border bg-surface-light hover:bg-surface-lighter"
              }`}
              style={
                isActive
                  ? { borderColor: accent, backgroundColor: `${accent}15` }
                  : undefined
              }
            >
              <div
                className="text-xs font-medium mb-0.5"
                style={isActive ? { color: accent } : { color: "#ccc" }}
              >
                {anim.label}
              </div>
              <div className="text-[10px] text-gray-500">{anim.preview}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
