import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import pickle
from pathlib import Path

# ============================================================
# Arguments
# ============================================================

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <capture.bin>")
    sys.exit(1)

filename = sys.argv[1]


# ============================================================
# Settings
# ============================================================

sample_rate = 100e6

# Voltage measured with your reference oscilloscope
known_voltage_peak = 0.200
known_voltage_pp = 2 * known_voltage_peak

x_length_us = 100


# ============================================================
# Read capture
# ============================================================

raw = np.fromfile(filename, dtype=np.uint8)

if len(raw) == 0:
    print(f"ERROR: No samples found in {filename}")
    sys.exit(1)

samples = raw.astype(np.float64)


# ============================================================
# Find ADC centre
# ============================================================

centre = np.mean(samples)

centred_samples = samples - centre


# ============================================================
# Find measured code amplitude
# ============================================================

low = np.percentile(samples, 1)
high = np.percentile(samples, 99)

code_pp = high - low


# ============================================================
# Calibration
# ============================================================

volts_per_code = known_voltage_pp / code_pp

voltage = centred_samples * volts_per_code


# ============================================================
# Time
# ============================================================

time_us = np.arange(len(samples)) / sample_rate * 1e6


# ============================================================
# Results
# ============================================================

print(f"File: {filename}")
print(f"Samples: {len(samples)}")

print(f"ADC centre: {centre:.2f} codes")
print(f"Low code: {low:.2f}")
print(f"High code: {high:.2f}")
print(f"Code Vpp: {code_pp:.2f}")

print(f"Calibration: {volts_per_code * 1000:.3f} mV/code")

print(f"Measured peak: {np.max(np.abs(voltage)):.4f} V")
print(f"Measured Vpp: {np.ptp(voltage):.4f} V")


# ============================================================
# Plot
# ============================================================

plt.plot(time_us, voltage, linewidth=0.8)

plt.xlabel("Time (µs)")
plt.ylabel("Input Voltage (V)")
plt.title(f"Oscilloscope Capture - {filename}")

frequency = 500e3
plt.xlim(0, (5 / frequency) * 1e6)
# plt.xlim(0, 5*600/100)

plt.grid(True)
plt.tight_layout()

# Save files
# ============================================================
# Save files
# ============================================================


BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR.parent / "Images"

# Create Images directory if it doesn't exist
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# Remove directory and extension from input filename
base = Path(filename).stem

png_file = IMAGE_DIR / f"{base}.png"
fig_file = IMAGE_DIR / f"{base}.fig"

plt.savefig(png_file, dpi=300)

with open(fig_file, "wb") as f:
    pickle.dump(plt.gcf(), f)

print(f"Saved PNG: {png_file}")
print(f"Saved FIG: {fig_file}")

plt.show()
