"use client";

interface ColorPickerProps {
  label: string;
  value: string;
  onChange: (color: string) => void;
  presets?: string[];
}

export function ColorPicker({ label, value, onChange, presets }: ColorPickerProps) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-xs text-gray-400 w-20 shrink-0">{label}</label>
      <div className="flex items-center gap-1.5">
        <div className="relative">
          <input
            type="color"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-7 h-7 rounded cursor-pointer border border-surface-border bg-transparent"
          />
        </div>
        <input
          type="text"
          value={value}
          onChange={(e) => {
            const v = e.target.value;
            if (/^#[0-9a-fA-F]{0,6}$/.test(v)) onChange(v);
          }}
          className="w-20 bg-surface border border-surface-border rounded px-2 py-1 text-xs font-mono text-white focus:outline-none"
        />
        {presets && (
          <div className="flex gap-1 ml-1">
            {presets.map((p) => (
              <button
                key={p}
                onClick={() => onChange(p)}
                className="w-5 h-5 rounded-sm border border-surface-border hover:scale-110 transition-transform"
                style={{ backgroundColor: p }}
                title={p}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
