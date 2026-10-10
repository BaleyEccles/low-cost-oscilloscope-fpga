import matplotlib.pyplot as plt
import numpy as np

# Read raw ADC bytes directly
samples = np.fromfile("../Data/tmp.bin", dtype=np.uint8)

# AD9484 running at 100 MS/s
sample_rate = 200e6

# Time axis
time = np.arange(len(samples)) / sample_rate
time_us = time * 1e6

print(f"Samples: {len(samples)}")
print(f"Sample rate: {sample_rate / 1e6:.2f} MS/s")
print(f"Sample period: {1 / sample_rate * 1e9:.2f} ns")

if len(samples) > 0:
    print(f"Capture time: {len(samples) / sample_rate * 1e6:.3f} us")
    print(f"Minimum ADC code: {samples.min()}")
    print(f"Maximum ADC code: {samples.max()}")
    print(f"Mean ADC code: {samples.mean():.2f}")

# Plot
plt.plot(time_us, samples, linewidth=0.8)

plt.xlabel("Time (µs)")
plt.ylabel("ADC Code")
plt.title("AD9484 Capture - 100 MS/s")

plt.ylim(0, 255)
plt.xlim(0, 2)
plt.grid(True)
plt.tight_layout()

plt.show()
