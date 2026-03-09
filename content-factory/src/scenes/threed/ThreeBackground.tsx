import React, { useRef, useMemo } from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import type { ThemeConfig } from "../../types/themes";

// Subtle wireframe shape — background decoration, not hero
const WireGeo: React.FC<{ color: string; frame: number }> = ({
  color,
  frame,
}) => {
  const ref = useRef<THREE.Mesh>(null);
  const t = frame * 0.006;

  useFrame(() => {
    if (!ref.current) return;
    ref.current.rotation.x = t * 0.5;
    ref.current.rotation.y = t * 0.7;
  });

  return (
    <mesh ref={ref}>
      <icosahedronGeometry args={[2.5, 1]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.8}
        wireframe
        transparent
        opacity={0.12}
        toneMapped={false}
      />
    </mesh>
  );
};

// Floating particles — sparse, elegant
const Particles: React.FC<{ count: number; color: string; frame: number }> = ({
  count,
  color,
  frame,
}) => {
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 16;
      arr[i * 3 + 1] = (Math.random() - 0.5) * 16;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 16;
    }
    return arr;
  }, [count]);

  const ref = useRef<THREE.Points>(null);

  useFrame(() => {
    if (!ref.current) return;
    ref.current.rotation.y = frame * 0.001;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
          count={count}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        color={color}
        size={0.04}
        transparent
        opacity={0.5}
        sizeAttenuation
      />
    </points>
  );
};

// Slow camera drift
const CameraRig: React.FC<{ frame: number }> = ({ frame }) => {
  const { camera } = useThree();
  const t = frame * 0.003;

  useFrame(() => {
    camera.position.x = Math.sin(t) * 7;
    camera.position.z = Math.cos(t) * 7;
    camera.position.y = 2 + Math.sin(t * 0.4) * 0.5;
    camera.lookAt(0, 0, 0);
  });

  return null;
};

const Scene: React.FC<{ accentColor: string; frame: number }> = ({
  accentColor,
  frame,
}) => (
  <>
    <CameraRig frame={frame} />
    <ambientLight intensity={0.1} />
    <WireGeo color={accentColor} frame={frame} />
    <Particles count={150} color={accentColor} frame={frame} />
  </>
);

export const ThreeBackground: React.FC<{ theme: ThemeConfig }> = ({
  theme,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const { colors } = theme;

  // Animated accent glow position
  const glowX = 50 + Math.sin(frame * 0.008) * 12;
  const glowY = 35 + Math.cos(frame * 0.006) * 8;

  return (
    <div style={{ position: "absolute", inset: 0 }}>
      {/* Base gradient */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at ${glowX}% ${glowY}%, ${colors.bgLight} 0%, ${colors.bg} 40%, ${colors.bgDark} 100%)`,
        }}
      />

      {/* 3D layer — subtle, behind everything */}
      <ThreeCanvas
        width={width}
        height={height}
        style={{ position: "absolute", inset: 0 }}
        camera={{ position: [7, 2, 0], fov: 50 }}
      >
        <Scene accentColor={colors.accent} frame={frame} />
      </ThreeCanvas>

      {/* Soft accent glow */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(circle at ${glowX}% ${glowY}%, ${colors.accent}15 0%, transparent 45%)`,
        }}
      />

      {/* Vignette */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at 50% 50%, transparent 30%, rgba(0,0,0,0.5) 100%)",
        }}
      />
    </div>
  );
};
