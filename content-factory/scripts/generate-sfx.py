"""Generate whoosh/swoosh transition sound effects using synthesis."""
import sys, io, os, struct, math, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SFX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "sfx")
os.makedirs(SFX_DIR, exist_ok=True)

SAMPLE_RATE = 44100

def generate_samples(duration_s, freq_start, freq_end, noise_amount=0.6, style="whoosh"):
    """Generate raw audio samples for a swoosh/whoosh sound."""
    n_samples = int(SAMPLE_RATE * duration_s)
    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        progress = i / n_samples

        # Envelope: quick attack, sustained, fade out
        if progress < 0.05:
            env = progress / 0.05
        elif progress < 0.4:
            env = 1.0
        else:
            env = max(0, 1.0 - (progress - 0.4) / 0.6)

        env = env ** 1.5  # Shape the envelope

        # Frequency sweep
        freq = freq_start + (freq_end - freq_start) * progress

        # Tone component (filtered sweep)
        tone = math.sin(2 * math.pi * freq * t) * 0.3

        # Noise component (the actual whoosh)
        noise = (random.random() * 2 - 1) * noise_amount

        # Bandpass-ish effect: mix noise with resonance
        if style == "whoosh":
            # Standard whoosh — more noise
            sample = (tone * 0.3 + noise * 0.7) * env
        elif style == "swoosh":
            # Swoosh — more tonal, higher pitch sweep
            sample = (tone * 0.5 + noise * 0.5) * env
        elif style == "impact":
            # Impact whoosh — sharp attack, bass thump
            bass = math.sin(2 * math.pi * 60 * t) * max(0, 1 - progress * 4) * 0.4
            sample = (tone * 0.3 + noise * 0.5 + bass) * env

        # Soft clip
        sample = max(-0.95, min(0.95, sample * 0.8))
        samples.append(sample)

    return samples


def write_wav(filename, samples):
    """Write samples to a WAV file."""
    path = os.path.join(SFX_DIR, filename)
    n = len(samples)
    with open(path, 'wb') as f:
        # WAV header
        f.write(b'RIFF')
        data_size = n * 2
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))  # chunk size
        f.write(struct.pack('<H', 1))   # PCM
        f.write(struct.pack('<H', 1))   # mono
        f.write(struct.pack('<I', SAMPLE_RATE))
        f.write(struct.pack('<I', SAMPLE_RATE * 2))  # byte rate
        f.write(struct.pack('<H', 2))   # block align
        f.write(struct.pack('<H', 16))  # bits per sample
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        for s in samples:
            val = int(s * 32767)
            val = max(-32768, min(32767, val))
            f.write(struct.pack('<h', val))
    print(f"  Generated: {path} ({n/SAMPLE_RATE:.2f}s)")


def main():
    print("[SFX] Generating transition sound effects...")

    # Whoosh 1: Standard fast whoosh (0.4s)
    samples = generate_samples(0.4, 800, 200, noise_amount=0.7, style="whoosh")
    write_wav("whoosh1.wav", samples)

    # Whoosh 2: Swoosh — tonal, slightly longer (0.5s)
    samples = generate_samples(0.5, 1200, 300, noise_amount=0.5, style="swoosh")
    write_wav("whoosh2.wav", samples)

    # Whoosh 3: Impact whoosh — bass thump + air (0.45s)
    samples = generate_samples(0.45, 600, 150, noise_amount=0.65, style="impact")
    write_wav("whoosh3.wav", samples)

    print("[SFX] Done! 3 sound effects generated in public/sfx/")


if __name__ == "__main__":
    main()
