import matplotlib.pyplot as plt
import numpy as np

# Read raw ADC bytes directly
samples = np.fromfile("../Data/500MSPS_test.bin", dtype=np.uint8)

# Set this to the actual ADC sample rate
sample_rate = 200e6  # 200 MS/s

if len(samples) == 0:
    raise ValueError("No samples were read from the file.")

# Basic information
print(f"Samples: {len(samples)}")
print(f"Sample rate: {sample_rate / 1e6:.2f} MS/s")
print(f"Sample period: {1 / sample_rate * 1e9:.2f} ns")
print(f"Capture time: {len(samples) / sample_rate * 1e6:.3f} us")
print(f"Minimum ADC code: {samples.min()}")
print(f"Maximum ADC code: {samples.max()}")
print(f"Mean ADC code: {samples.mean():.2f}")

# Time axis
time = np.arange(len(samples)) / sample_rate
time_us = time * 1e6

# Remove DC offset
signal = samples.astype(float)
signal -= np.mean(signal)

# Apply a Hann window to reduce spectral leakage
window = np.hanning(len(signal))
windowed_signal = signal * window

# FFT
fft_result = np.fft.rfft(windowed_signal)
frequencies = np.fft.rfftfreq(len(signal), d=1 / sample_rate)

# Magnitude spectrum
magnitude = np.abs(fft_result)

# Ignore DC when finding the dominant frequency
if len(magnitude) > 1:
    peak_index = np.argmax(magnitude[1:]) + 1
else:
    peak_index = 0

peak_frequency = frequencies[peak_index]

print(f"FFT frequency resolution: {sample_rate / len(signal):.2f} Hz")
print(f"Peak frequency: {peak_frequency / 1e6:.6f} MHz")

# Plot time-domain signal and FFT
fig, axes = plt.subplots(2, 1, figsize=(10, 8))

# Time-domain plot
axes[0].plot(time_us, samples, linewidth=0.8)
axes[0].set_xlabel("Time (µs)")
axes[0].set_ylabel("ADC Code")
axes[0].set_title("AD9484 Capture - Time Domain")
axes[0].set_ylim(0, 255)
axes[0].grid(True)

# Frequency-domain plot
axes[1].plot(frequencies / 1e6, magnitude, linewidth=0.8)
axes[1].axvline(
    peak_frequency / 1e6,
    color="red",
    linestyle="--",
    label=f"Peak: {peak_frequency / 1e6:.6f} MHz"
)

axes[1].set_xlabel("Frequency (MHz)")
axes[1].set_ylabel("Magnitude")
axes[1].set_title("FFT Frequency Spectrum")
axes[1].set_xlim(0, sample_rate / 2 / 1e6)  # 0 to Nyquist frequency
axes[1].grid(True)
axes[1].legend()

plt.tight_layout()
plt.show()
