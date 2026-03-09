"use client";

interface FontSelectorProps {
  label: string;
  value: string;
  onChange: (font: string) => void;
}

const FONTS = [
  "Segoe UI",
  "Arial",
  "Helvetica",
  "Inter",
  "Roboto",
  "SF Pro",
  "Cascadia Code",
  "Consolas",
  "Fira Code",
  "JetBrains Mono",
  "Courier New",
  "Georgia",
  "Times New Roman",
];

export function FontSelector({ label, value, onChange }: FontSelectorProps) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-xs text-gray-400 w-20 shrink-0">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="flex-1 bg-surface border border-surface-border rounded px-2 py-1.5 text-xs text-white focus:outline-none"
        style={{ fontFamily: value }}
      >
        {FONTS.map((f) => (
          <option key={f} value={f} style={{ fontFamily: f }}>
            {f}
          </option>
        ))}
      </select>
    </div>
  );
}
