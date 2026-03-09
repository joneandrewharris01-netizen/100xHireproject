/** @type {import('next').NextConfig} */
const nextConfig = {
  // Exclude Remotion files from Next.js compilation
  webpack: (config) => {
    // Remotion uses its own bundler — don't let Next.js process it
    config.externals = config.externals || [];
    return config;
  },
  // Allow serving video files from out/ and audio from public/
  async headers() {
    return [
      {
        source: "/api/:path*",
        headers: [
          { key: "Cache-Control", value: "no-store" },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
