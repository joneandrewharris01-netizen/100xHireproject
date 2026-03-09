"use client";

interface BrandProfile {
  badge: string;
  colors: {
    accent: string;
    accentLight?: string;
    bg: string;
    text: string;
    textSoft?: string;
    termBg?: string;
    termBorder?: string;
  };
  fonts: {
    heading: string;
    body: string;
    mono: string;
  };
  captions: {
    fontSize: number;
    activeFontSize: number;
    top: number;
  };
  animation?: string;
}

interface BrandPreviewProps {
  profile: BrandProfile;
}

export function BrandPreview({ profile }: BrandPreviewProps) {
  const { badge, colors, fonts } = profile;

  // Mini 270x480 preview that mimics the video look
  return (
    <div>
      <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">
        Live Preview
      </label>
      <div
        className="w-[270px] h-[480px] rounded-xl overflow-hidden border border-surface-border relative"
        style={{
          backgroundColor: colors.bg,
          fontFamily: fonts.body,
        }}
      >
        {/* Gradient overlay */}
        <div
          className="absolute inset-0"
          style={{
            background: `radial-gradient(ellipse at 50% 30%, ${colors.accent}15, transparent 70%)`,
          }}
        />

        {/* Badge */}
        <div className="absolute top-4 left-4 right-4 z-10">
          <div
            className="inline-block px-3 py-1 rounded-full text-xs font-bold"
            style={{
              background: `linear-gradient(135deg, ${colors.accent}, ${colors.accentLight || colors.accent})`,
              color: colors.bg,
            }}
          >
            {badge || "Brand Name"}
          </div>
        </div>

        {/* Terminal block preview */}
        <div className="absolute top-16 left-4 right-4 z-10">
          <div
            className="rounded-lg p-3 border"
            style={{
              backgroundColor: colors.termBg || "#0A0E16",
              borderColor: colors.termBorder || "#1E2A3A",
            }}
          >
            <div className="flex gap-1.5 mb-2">
              <div className="w-2 h-2 rounded-full bg-red-400" />
              <div className="w-2 h-2 rounded-full bg-yellow-400" />
              <div className="w-2 h-2 rounded-full bg-green-400" />
            </div>
            <div className="space-y-1">
              <p
                className="text-[10px]"
                style={{ fontFamily: fonts.mono, color: colors.accent }}
              >
                $ automation --start
              </p>
              <p
                className="text-[10px]"
                style={{ fontFamily: fonts.mono, color: colors.textSoft || "#C8D0E0" }}
              >
                Connecting to API...
              </p>
              <p
                className="text-[10px]"
                style={{ fontFamily: fonts.mono, color: colors.accent }}
              >
                Done. Saved $4,000/mo
              </p>
            </div>
          </div>
        </div>

        {/* Data card preview */}
        <div className="absolute top-52 left-4 right-4 z-10">
          <div
            className="rounded-lg p-3 border"
            style={{
              backgroundColor: `${colors.bg}CC`,
              borderColor: `${colors.accent}30`,
            }}
          >
            <p
              className="text-[10px] mb-1"
              style={{ fontFamily: fonts.heading, color: colors.textSoft || "#C8D0E0" }}
            >
              Monthly Savings
            </p>
            <p
              className="text-2xl font-bold"
              style={{ fontFamily: fonts.heading, color: colors.accent }}
            >
              $4,000
            </p>
          </div>
        </div>

        {/* Caption preview */}
        <div className="absolute bottom-16 left-4 right-4 z-10 text-center">
          <span
            className="font-bold"
            style={{
              fontSize: "16px",
              color: colors.accent,
              fontFamily: fonts.heading,
              textShadow: `0 0 20px ${colors.accent}60`,
            }}
          >
            This AI tool
          </span>{" "}
          <span
            style={{
              fontSize: "13px",
              color: `${colors.text}80`,
              fontFamily: fonts.heading,
            }}
          >
            feels illegal
          </span>
        </div>

        {/* CTA preview */}
        <div className="absolute bottom-4 left-4 right-4 z-10 text-center">
          <div
            className="rounded-lg py-2 text-xs font-bold"
            style={{
              background: `linear-gradient(135deg, ${colors.accent}, ${colors.accentLight || colors.accent})`,
              color: colors.bg,
            }}
          >
            Follow + DM
          </div>
        </div>
      </div>
    </div>
  );
}
