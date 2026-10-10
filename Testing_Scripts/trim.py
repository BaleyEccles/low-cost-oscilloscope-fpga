import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# Settings
# ============================================================

sample_rate = 100e6

start_sample = 50*100
end_sample = 254*100


# ============================================================
# Load original capture
# ============================================================

raw = np.fromfile(
    "../Data/200MSPS_5k_0V_0.41V_step.bin",
    dtype=np.uint8
)


# ============================================================
# Trim data
# ============================================================

trimmed = raw[start_sample:end_sample]


# ============================================================
# Time axes
# ============================================================

time_us = np.arange(len(raw)) / sample_rate * 1e6

trimmed_time_us = (
    np.arange(len(trimmed)) / sample_rate * 1e6
)


# ============================================================
# Plot full capture
# ============================================================

plt.figure()

plt.plot(
    time_us,
    raw
)

plt.axvline(
    start_sample / sample_rate * 1e6,
    linestyle="--",
    label="Start"
)

plt.axvline(
    end_sample / sample_rate * 1e6,
    linestyle="--",
    label="End"
)

plt.xlabel("Time (µs)")
plt.ylabel("ADC Code")

plt.title("Full Step Capture")

plt.grid(True)
plt.legend()
plt.tight_layout()


# ============================================================
# Plot trimmed capture
# ============================================================

plt.figure()

plt.plot(
    trimmed_time_us,
    trimmed
)

plt.xlabel("Time (µs)")
plt.ylabel("ADC Code")

plt.title("Trimmed Step Response")

plt.grid(True)
plt.tight_layout()


# ============================================================
# Save trimmed capture
# ============================================================

#trimmed.tofile("../Data/200MSPS_step.bin")
print("Saved to ../Data/200MSPS_step.bin")

print(f"Original samples: {len(raw)}")
print(f"Saved samples: {len(trimmed)}")

print(
    f"Start time: "
    f"{start_sample / sample_rate * 1e6:.2f} us"
)

print(
    f"End time: "
    f"{end_sample / sample_rate * 1e6:.2f} us"
)




# ============================================================
# Show plots
# ============================================================

plt.show()
