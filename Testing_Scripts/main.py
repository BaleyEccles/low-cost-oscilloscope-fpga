from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import pickle
import gc

# Configuration

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "Data"
IMAGE_DIR = BASE_DIR.parent / "Images"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 100e6
ADC_BITS = 8

# Oscilloscope input full-scale range.
# Change this to your actual calibrated full-scale input range.

# Calibration function
def calibrate_volts_per_code(
    raw,
    known_peak_voltage,
    frequency,
    sample_rate=100e6,
):
    """
    Find volts per ADC code using a known sine-wave input.

    raw:
        uint8 ADC samples

    known_peak_voltage:
        Actual input peak voltage measured at the BNC

    frequency:
        Calibration sine-wave frequency
    """

    samples = raw.astype(np.float64)

    t = np.arange(len(samples)) / sample_rate

    omega = 2 * np.pi * frequency

    # Fit:
    # x(t) = a sin(wt) + b cos(wt) + c
    A = np.column_stack([
        np.sin(omega * t),
        np.cos(omega * t),
        np.ones_like(t)
    ])

    a, b, dc = np.linalg.lstsq(
        A,
        samples,
        rcond=None
    )[0]

    amplitude_codes = np.sqrt(a**2 + b**2)

    volts_per_code = (
        known_peak_voltage
        / amplitude_codes
    )

    print(f"ADC centre: {dc:.3f} codes")
    print(f"ADC amplitude: {amplitude_codes:.3f} codes")
    print(
        f"Calibration: "
        f"{volts_per_code * 1000:.6f} mV/code"
    )
    full_scale_range = 255*volts_per_code
    print(f"full_scale_range: {full_scale_range:.3f} V")
    
    return volts_per_code, dc, full_scale_range

raw = np.fromfile(
    "../Data/100MSPS_0.2V_1M_sin.bin",
    dtype=np.uint8
)
    
VOLTS_PER_CODE, ADC_ZERO_CODE, FULL_SCALE_RANGE = calibrate_volts_per_code(
    raw,
    known_peak_voltage=0.2,
    frequency=1e6,
    sample_rate=100e6
)

# General functions
def load_capture(
    filename,
    volts_per_code=VOLTS_PER_CODE,
    zero_code=ADC_ZERO_CODE,
    remove_mean=False,
):
    """
    Load an unsigned 8-bit ADC capture and convert it to volts.
    """

    path = Path(filename)

    if not path.is_absolute():
        path = DATA_DIR / path

    raw = np.fromfile(path, dtype=np.uint8)

    if len(raw) == 0:
        raise ValueError(f"No samples found in {path}")

    voltage = (raw.astype(np.float64) - zero_code) * volts_per_code

    if remove_mean:
        voltage -= np.mean(voltage)

    return voltage


def rms(x):
    """
    Root-mean-square of a waveform.
    """

    x = np.asarray(x, dtype=np.float64)

    return np.sqrt(np.mean(x**2))


def time_axis(number_samples, sample_rate=SAMPLE_RATE):
    """
    Generate time axis in seconds.
    """

    return np.arange(number_samples) / sample_rate


import pickle

def save_plot(name):
    """
    Save current plot into ../Images as:
        .png
        .pdf
        .fig
    """

    png_file = IMAGE_DIR / f"{name}.png"
    pdf_file = IMAGE_DIR / f"{name}.pdf"
    fig_file = IMAGE_DIR / f"{name}.fig"

    fig = plt.gcf()

    # PNG
    fig.savefig(
        png_file,
        dpi=300,
        bbox_inches="tight"
    )

    # Vector PDF for LaTeX/thesis
    fig.savefig(
        pdf_file,
        bbox_inches="tight"
    )

    # Re-openable Matplotlib figure
    with open(fig_file, "wb") as f:
        pickle.dump(
            fig,
            f,
            protocol=pickle.HIGHEST_PROTOCOL
        )

    print(f"Saved PNG: {png_file}")
    print(f"Saved PDF: {pdf_file}")
    print(f"Saved FIG: {fig_file}")

# Best-fit sine wave


def fit_sine(
    x,
    frequency,
    sample_rate=SAMPLE_RATE,
):
    """
    Calculate a least-squares best-fit sine wave.

    Model:

        x'(t) = a sin(wt) + b cos(wt) + c

    Returns:
        fitted waveform
        peak amplitude
        RMS amplitude
        phase
        DC offset
    """

    x = np.asarray(x, dtype=np.float64)

    t = time_axis(len(x), sample_rate)

    omega = 2 * np.pi * frequency

    A = np.column_stack(
        (
            np.sin(omega * t),
            np.cos(omega * t),
            np.ones_like(t),
        )
    )

    a, b, dc = np.linalg.lstsq(A, x, rcond=None)[0]

    fitted = a * np.sin(omega * t) + b * np.cos(omega * t) + dc

    amplitude_peak = np.hypot(a, b)

    amplitude_rms = amplitude_peak / np.sqrt(2)

    phase = np.arctan2(b, a)

    return {
        "fitted": fitted,
        "peak": amplitude_peak,
        "rms": amplitude_rms,
        "phase_rad": phase,
        "dc": dc,
    }


# DC Testing


def dc_test(x):
    """
    Calculate DC offset and noise statistics.
    """

    x = np.asarray(x, dtype=np.float64)

    return {
        "mean_V": np.mean(x),
        "std_V": np.std(x, ddof=1),
        "rms_V": rms(x),
        "min_V": np.min(x),
        "max_V": np.max(x),
        "vpp_V": np.ptp(x),
    }


# Frequency Response


def frequency_response(
    captures,
    reference_capture,
    reference_frequency=1e6,
    input_amplitude=0.200,
    sample_rate=SAMPLE_RATE,
):
    """
    Calculate frequency response.

    captures should be:

        {
            frequency: waveform,
            frequency: waveform,
            ...
        }

    Gain:

        G(f) = Vmeasured / Vinput

    Normalised gain:

        GdB = 20 log10(G(f) / G(ref))

    Gain error:

        error = (G(f) - G(ref)) / G(ref)
    """

    reference_fit = fit_sine(reference_capture, reference_frequency, sample_rate)

    reference_measured = reference_fit["peak"]

    reference_gain = reference_measured / input_amplitude

    results = []

    for frequency in sorted(captures):

        fit = fit_sine(captures[frequency], frequency, sample_rate)

        measured_voltage = fit["peak"]

        gain = measured_voltage / input_amplitude

        gain_db = 20 * np.log10(gain / reference_gain)

        gain_error = (gain - reference_gain) / reference_gain

        results.append(
            {
                "frequency_Hz": frequency,
                "measured_peak_V": measured_voltage,
                "gain": gain,
                "gain_dB": gain_db,
                "gain_error": gain_error,
            }
        )

    bandwidth = estimate_3db_bandwidth(results)

    return {
        "reference_frequency_Hz": reference_frequency,
        "reference_measured_peak_V": reference_measured,
        "reference_gain": reference_gain,
        "results": results,
        "bandwidth_3dB_Hz": bandwidth,
    }


def estimate_3db_bandwidth(results):
    """
    Estimate first -3 dB crossing.

    Interpolation is performed on a logarithmic
    frequency scale.
    """

    frequencies = np.array([r["frequency_Hz"] for r in results], dtype=float)

    gains_db = np.array([r["gain_dB"] for r in results], dtype=float)

    for i in range(1, len(frequencies)):

        if gains_db[i - 1] > -3 and gains_db[i] <= -3:

            x1 = np.log10(frequencies[i - 1])

            x2 = np.log10(frequencies[i])

            y1 = gains_db[i - 1]
            y2 = gains_db[i]

            x = x1 + (-3 - y1) * (x2 - x1) / (y2 - y1)

            return 10**x

    return None


def plot_frequency_response(result):

    rows = result["results"]

    frequency = np.array([r["frequency_Hz"] for r in rows])

    gain_db = np.array([r["gain_dB"] for r in rows])

    plt.figure()

    plt.semilogx(frequency, gain_db, "o-")

    plt.axhline(-3, linestyle="--", label="-3 dB")

    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Normalised Gain (dB)")

    plt.title("Oscilloscope Frequency Response At 100MSPS")

    plt.grid(True, which="both")

    plt.legend()

    plt.tight_layout()

    save_plot("100MSPS_frequency_response")


# Step Response


def step_response(
    x,
    step_amplitude,
    polarity="negative",
    final_value=0.0,
    settling_fraction=0.02,
    sample_rate=SAMPLE_RATE,
):
    """
    Analyse an AC-coupled step response.

    Parameters
    ----------
    x : array
        Captured waveform in volts.

    step_amplitude : float
        Magnitude of the applied step in volts.
        Example: 0.41 for a 0.41 V step.

    polarity : str
        "positive", "negative", or "auto".

        For your falling-edge AC-coupled response use:
            polarity="negative"

    final_value : float
        Value that the AC-coupled waveform should eventually
        settle to. Normally 0 V.

    settling_fraction : float
        Settling band as a fraction of the step amplitude.

        0.02 = 2%
        0.05 = 5%
        0.10 = 10%

    sample_rate : float
        Sampling frequency in samples/s.


    Returns
    -------
    Dictionary containing:
        polarity
        baseline_V
        reference_50_V
        peak_V
        peak_excursion_V
        peak_time_s
        t50_s
        settling_band_V
        settling_time_s
        settling_duration_s
        settling_error_ratio
        settling_error_percent
        peak_error_percent
        overshoot_ratio
        overshoot_percent
    """

    x = np.asarray(x, dtype=np.float64)

    if len(x) < 3:
        raise ValueError("Step capture is too short.")

    if step_amplitude <= 0:
        raise ValueError(
            "step_amplitude must be greater than zero."
        )

    if settling_fraction <= 0:
        raise ValueError(
            "settling_fraction must be greater than zero."
        )

    # ========================================================
    # Time axis
    # ========================================================

    t = np.arange(len(x)) / sample_rate


    # ========================================================
    # Determine edge polarity
    # ========================================================

    diff = np.diff(x)

    if polarity == "auto":

        positive_change = np.max(diff)
        negative_change = abs(np.min(diff))

        if negative_change > positive_change:
            polarity = "negative"
        else:
            polarity = "positive"

    if polarity == "negative":

        direction = -1

        # Strongest falling edge
        edge_index = np.argmin(diff) + 1

    elif polarity == "positive":

        direction = 1

        # Strongest rising edge
        edge_index = np.argmax(diff) + 1

    else:

        raise ValueError(
            'polarity must be '
            '"positive", "negative", or "auto"'
        )


    # ========================================================
    # Diagnostic pre-step baseline
    #
    # This is NOT used to shift the waveform.
    # It is only reported so that any offset can be seen.
    # ========================================================

    if edge_index > 0:

        baseline = np.mean(
            x[:edge_index]
        )

    else:

        baseline = x[0]


    # ========================================================
    # 50% reference level
    #
    # Negative:
    #
    #     0 V -> -0.41 V
    #
    #     V50 = -0.205 V
    #
    # Positive:
    #
    #     0 V -> +0.41 V
    #
    #     V50 = +0.205 V
    # ========================================================

    reference_50 = (
        final_value
        + direction
        * 0.5
        * step_amplitude
    )


    # ========================================================
    # Find 50% crossing
    # ========================================================

    if polarity == "negative":

        crossings = np.where(
            (x[:-1] > reference_50)
            & (x[1:] <= reference_50)
        )[0]

    else:

        crossings = np.where(
            (x[:-1] < reference_50)
            & (x[1:] >= reference_50)
        )[0]


    # Use the crossing closest to the detected edge
    if len(crossings) > 0:

        crossing_index = crossings[
            np.argmin(
                np.abs(
                    crossings - edge_index
                )
            )
        ]

        t50_index = crossing_index + 1

    else:

        t50_index = None


    # ========================================================
    # Find peak
    #
    # Search after the 50% crossing.
    # ========================================================

    if t50_index is not None:
        search_start = t50_index
    else:
        search_start = edge_index

    if polarity == "negative":

        relative_peak_index = np.argmin(
            x[search_start:]
        )

    else:

        relative_peak_index = np.argmax(
            x[search_start:]
        )

    peak_index = (
        search_start
        + relative_peak_index
    )

    peak_value = x[peak_index]


    # ========================================================
    # Peak excursion from final value
    # ========================================================

    peak_excursion = abs(
        peak_value - final_value
    )


    # ========================================================
    # Peak amplitude error
    #
    # Positive  -> larger than intended
    # Negative  -> smaller than intended
    # ========================================================

    peak_error = (
        peak_excursion
        - step_amplitude
    ) / step_amplitude


    # ========================================================
    # Overshoot
    #
    # Overshoot cannot be negative.
    #
    # Example:
    #
    # nominal = 0.410 V
    # peak    = 0.426 V
    #
    # overshoot = 3.9 %
    # ========================================================

    overshoot = max(
        0.0,
        peak_error
    )


    # ========================================================
    # Settling band
    # ========================================================

    settling_band = (
        settling_fraction
        * step_amplitude
    )

    lower_limit = (
        final_value
        - settling_band
    )

    upper_limit = (
        final_value
        + settling_band
    )


    # ========================================================
    # Determine which samples are inside settling band
    # ========================================================

    inside_band = (
        (x >= lower_limit)
        & (x <= upper_limit)
    )


    # ========================================================
    # Find first point after peak where the waveform enters
    # the band and remains there for the rest of the capture.
    # ========================================================

    remains_inside = np.logical_and.accumulate(
        inside_band[::-1]
    )[::-1]

    candidates = np.where(
        remains_inside
        & (
            np.arange(len(x))
            >= peak_index
        )
    )[0]


    if len(candidates) > 0:

        settling_index = candidates[0]

    else:

        settling_index = None


    # ========================================================
    # Settling time / duration
    # ========================================================

    if settling_index is not None:

        settling_time = t[
            settling_index
        ]

        if t50_index is not None:

            settling_duration = (
                settling_index
                - t50_index
            ) / sample_rate

        else:

            settling_duration = None

    else:

        settling_time = None
        settling_duration = None


    # ========================================================
    # Settling error
    #
    # Maximum remaining deviation after settling.
    # ========================================================

    if settling_index is not None:

        settling_error = (
            np.max(
                np.abs(
                    x[settling_index:]
                    - final_value
                )
            )
            / step_amplitude
        )

    else:

        settling_error = None


    # ========================================================
    # Return results
    # ========================================================

    return {
        "polarity":
            polarity,

        "baseline_V":
            baseline,

        "reference_50_V":
            reference_50,

        "peak_V":
            peak_value,

        "peak_excursion_V":
            peak_excursion,

        "peak_time_s":
            t[peak_index],

        "t50_s":
            (
                None
                if t50_index is None
                else t[t50_index]
            ),

        "settling_band_V":
            settling_band,

        "settling_band_low_V":
            lower_limit,

        "settling_band_high_V":
            upper_limit,

        "settling_time_s":
            settling_time,

        "settling_duration_s":
            settling_duration,

        "settling_error_ratio":
            settling_error,

        "settling_error_percent":
            (
                None
                if settling_error is None
                else settling_error * 100
            ),

        "peak_error_percent":
            peak_error * 100,

        "overshoot_ratio":
            overshoot,

        "overshoot_percent":
            overshoot * 100,
    }


def plot_step_response(
    x,
    result,
    sample_rate=SAMPLE_RATE,
):

    time_us = time_axis(len(x), sample_rate) * 1e6

    plt.figure()

    plt.plot(time_us, x, linewidth=0.8)

    plt.axhline(0, linewidth=0.8)

    if result["t50_s"] is not None:

        plt.axvline(result["t50_s"] * 1e6, linestyle="--", label="50% instant")

    if result["settling_time_s"] is not None:

        plt.axvline(result["settling_time_s"] * 1e6, linestyle="--", label="Settled")

    band = result["settling_band_V"]

    plt.axhline(band, linestyle=":")

    plt.axhline(-band, linestyle=":", label="Settling band")

    plt.xlabel("Time (µs)")
    plt.ylabel("Voltage (V)")

    plt.title("Step Response of 100MSPS Oscilloscope")

    plt.grid(True)

    plt.legend()

    plt.tight_layout()

    save_plot("100MSPS_step_response")


# Noise Floor


def noise_floor(x_a, x_b):
    """
    Calculate:

        eta^2 =
        1/(2M) sum((xa[n] - xb[n])^2)
    """

    M = min(len(x_a), len(x_b))

    if M == 0:
        raise ValueError("Noise captures contain no samples")

    difference = np.asarray(x_a[:M]) - np.asarray(x_b[:M])

    eta_squared = np.sum(difference**2) / (2 * M)

    eta = np.sqrt(eta_squared)

    return {
        "samples": M,
        "mean_squared_noise_V2": eta_squared,
        "noise_rms_V": eta,
    }


# SINAD and NAD


def sinad(
    x,
    frequency,
    sample_rate=SAMPLE_RATE,
):
    """
    Calculate NAD using the difference between
    the measured waveform and the best-fit sine.

        NAD =
        sqrt(
            1/M sum((x[n] - x'[n])^2)
        )

    Then:

        SINAD = A_rms / NAD
    """

    fit = fit_sine(x, frequency, sample_rate)

    residual = np.asarray(x) - fit["fitted"]

    nad = rms(residual)

    signal_rms = fit["rms"]

    sinad_ratio = signal_rms / nad

    sinad_db = 20 * np.log10(sinad_ratio)

    return {
        "signal_peak_V": fit["peak"],
        "signal_rms_V": signal_rms,
        "NAD_V_rms": nad,
        "SINAD_ratio": sinad_ratio,
        "SINAD_dB": sinad_db,
        "fitted": fit["fitted"],
        "residual": residual,
    }


# THD
def thd_fft(
    x,
    fundamental_frequency,
    max_harmonic=5,
    sample_rate=SAMPLE_RATE,
    zero_pad_factor=8,
):
    """
    Calculate THD using a Fourier transform.

        THD =
        sqrt(V2^2 + V3^2 + ... + VN^2) / V1

    A Hann window and zero padding are used to
    reduce FFT leakage/scalloping effects.
    """

    x = np.asarray(x, dtype=np.float64)

    x = x - np.mean(x)

    N = len(x)

    window = np.hanning(N)

    n_fft = int(2 ** np.ceil(np.log2(N * zero_pad_factor)))

    spectrum = np.fft.rfft(x * window, n=n_fft)

    frequencies = np.fft.rfftfreq(n_fft, d=1 / sample_rate)

    magnitude = np.abs(spectrum)

    bin_width = sample_rate / n_fft

    search_width = max(3 * bin_width, fundamental_frequency * 0.01)

    harmonic_amplitudes = []

    for harmonic in range(1, max_harmonic + 1):
        target_frequency = harmonic * fundamental_frequency

        if target_frequency >= sample_rate / 2:
            break

        mask = np.abs(frequencies - target_frequency) <= search_width

        if not np.any(mask):
            break

        amplitude = np.max(magnitude[mask])
        print(f"harmonic {harmonic} ({target_frequency}) amplitude = {amplitude}")

        harmonic_amplitudes.append(amplitude)

    if len(harmonic_amplitudes) < 2:

        raise ValueError("Not enough harmonics below Nyquist")

    V1 = harmonic_amplitudes[0]

    harmonic_power = np.sum(np.square(harmonic_amplitudes[1:]))

    thd = np.sqrt(harmonic_power) / V1

    return {
        "THD_ratio": thd,
        "THD_percent": 100 * thd,
        "THD_dB": 20 * np.log10(thd),
        "harmonic_amplitudes_relative": np.array(harmonic_amplitudes) / V1,
    }


# SNR


def snr_from_nad_thd(
    nad,
    signal_rms,
    thd_ratio,
):
    """
    Calculate noise:

        eta =
        sqrt(
            NAD^2
            - A_rms^2 THD^2
        )

    Then:

        SNR = A_rms / eta
    """
    print(f"NAD: {nad}")
    print(f"RMS signal: {signal_rms}")
    print(f"THD Ratio: {thd_ratio}")
    
    harmonic_rms = signal_rms * thd_ratio

    noise_squared = nad**2 - harmonic_rms**2


    if noise_squared <= 0:

        raise ValueError("Calculated noise power <= 0. " "Check NAD and THD.")

    noise_rms = np.sqrt(noise_squared)
    print(f"Noise rms (eta) {noise_rms}")

    snr_ratio = signal_rms / noise_rms
    print(f"SNR {snr_ratio}")

    snr_db = 20 * np.log10(snr_ratio)
    print(f"SNR (dB) {snr_db}")

    return {
        "noise_rms_V": noise_rms,
        "SNR_ratio": snr_ratio,
        "SNR_dB": snr_db,
    }


# ENOB

def enob(
    nad,
    full_scale_range=FULL_SCALE_RANGE,
):
    """
    Calculate:

        ENOB =
        log2(
            FSR /
            (NAD sqrt(12))
        )
    """

    enob_bits = np.log2(full_scale_range / (nad * np.sqrt(12)))

    return {
        "ENOB_bits": enob_bits,
        "FSR_V": full_scale_range,
        "NAD_V_rms": nad,
    }

def plot_fft(
    x,
    sample_rate=SAMPLE_RATE,
    max_frequency=10e6,
):
    x = np.asarray(x, dtype=np.float64)

    # Remove DC
    x = x - np.mean(x)

    N = len(x)

    # Window to reduce spectral leakage
    window = np.hanning(N)
    x_windowed = x * window

    # FFT
    spectrum = np.fft.rfft(x_windowed)
    frequency = np.fft.rfftfreq(N, d=1 / sample_rate)

    # Correct for window gain and convert to peak voltage
    magnitude = 2 * np.abs(spectrum) / np.sum(window)

    # Convert to dB relative to 1 V
    magnitude_db = 20 * np.log10(np.maximum(magnitude, 1e-15))

    plt.figure()

    plt.plot(
        frequency / 1e6,
        magnitude_db,
        linewidth=0.8
    )

    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Magnitude (dBV)")
    plt.title("FFT of 1.1 MHz, 1V Sine Wave at 100MSPS")

    plt.xlim(0, max_frequency / 1e6)

    plt.grid(True)
    plt.tight_layout()

    save_plot("100MSPS_1V_1.1M_FFT")
    
def plot_all_captures(pattern="**/*.bin"):
    """
    Plot all matching binary captures in ../Data
    and save them using save_plot().

    Examples:
        plot_all_captures("**/*.bin")
        plot_all_captures("**/*step*.bin")
        plot_all_captures("**/*500k*.bin")
    """

    files = sorted(DATA_DIR.glob(pattern))

    if not files:
        print(f"No files found matching: {pattern}")
        return

    print(f"Found {len(files)} files")

    for filename in files:

        raw = np.fromfile(
            filename,
            dtype=np.uint8
        )

        if len(raw) == 0:
            print(f"Skipping empty file: {filename}")
            continue

        # Convert ADC codes to voltage
        voltage = (
            raw.astype(np.float64)
            - ADC_ZERO_CODE
        ) * VOLTS_PER_CODE

        # Time axis in microseconds
        time_us = (
            np.arange(len(raw))
            / SAMPLE_RATE
            * 1e6
        )

        # Create plot
        plt.figure()

        plt.plot(
            time_us,
            voltage,
            linewidth=0.8
        )

        plt.xlabel("Time (µs)")
        plt.ylabel("Input Voltage (V)")

        plt.title(
            f"Oscilloscope Capture - {filename.name}"
        )

        plt.grid(True)
        plt.tight_layout()

        # Use filename without .bin
        base = filename.stem

        save_plot(base)

        print(
            f"{filename.name}: "
            f"{len(raw)} samples, "
            f"{len(raw) / SAMPLE_RATE * 1e6:.2f} us"
        )

        # Free matplotlib memory
        plt.close()

        # Free arrays
        del raw
        del voltage
        del time_us



def main():
    print("")
    
    # DC TEST
    dc_captures = ["100MSPS_0.0VDC.bin", "100MSPS_0.2VDC.bin", "100MSPS_0.4VDC.bin"]
    for capture in dc_captures:
        dc = load_capture(
            capture
        )
        result = dc_test(dc)

        print(f"\nDC TEST: {capture}")
        for key, value in result.items():
            print(f"{key}: {value}")

        # NOISE FLOOR

        noise = load_capture(
            capture
        )
        
        half = len(noise) // 2
        
        noise_a = noise[:half]
        noise_b = noise[half:half * 2]
        
        result = noise_floor(
            noise_a,
            noise_b
        )
        
        print("\nNOISE FLOOR")
        
        for key, value in result.items():
            print(f"{key}: {value}")

    # SINAD
    wave = load_capture(
        "100MSPS_1V_1.1M_sin.bin"
    )

    sinad_result = sinad(
        wave,
        1.1e6
    )

    print("\nSINAD")

    print(
        f"NAD = "
        f"{sinad_result['NAD_V_rms']:.6f} V RMS"
    )

    print(
        f"SINAD = "
        f"{sinad_result['SINAD_dB']:.2f} dB"
    )

    enob_result = enob(
        sinad_result["NAD_V_rms"]
    )

    print(
        f"ENOB = "
        f"{enob_result['ENOB_bits']:.2f} bits"
    )

    # THD + SNR
    wave = load_capture(
        "100MSPS_1V_1.1M_sin.bin"
    )

    thd_result = thd_fft(
        wave,
        1.1e6,
        max_harmonic=5
    )

    nad_result = sinad(
        wave,
        1.1e6,
    )

    snr_result = snr_from_nad_thd(
        nad_result["NAD_V_rms"],
        nad_result["signal_rms_V"],
        thd_result["THD_ratio"]
    )

    print("\nTHD")

    print(
        f"THD = "
        f"{thd_result['THD_percent']:.3f} %"
    )

    print(
        f"THD = "
        f"{thd_result['THD_dB']:.2f} dB"
    )

    print("\nSNR")

    print(
        f"SNR = "
        f"{snr_result['SNR_dB']:.2f} dB"
    )

    wave = load_capture(
        "100MSPS_1V_1.1M_sin.bin"
    )
    
    plot_fft(
        wave,
        max_frequency=5e6
    )

    # STEP RESPONSE

    wave = load_capture(
        "100MSPS_step.bin"
    )

    result = step_response(
        wave,
        step_amplitude=0.41,
        polarity="negative",
        final_value=0.0,
        settling_fraction=0.02
    )

    print("\nSTEP RESPONSE")

    for key, value in result.items():
        print(f"{key}: {value}")

    plot_step_response(
        wave,
        result
        )
    
    # FREQUENCY RESPONSE

    files = {
        1e3:     "100MSPS_0.2V_1k_sin.bin",
        2e3:     "100MSPS_0.2V_2k_sin.bin",
        5e3:     "100MSPS_0.2V_5k_sin.bin",
        10e3:    "100MSPS_0.2V_10k_sin.bin",
        20e3:    "100MSPS_0.2V_20k_sin.bin",
        50e3:    "100MSPS_0.2V_50k_sin.bin",
    
        60e3:    "100MSPS_0.2V_60k_sin.bin",
        75e3:    "100MSPS_0.2V_75k_sin.bin",
        80e3:    "100MSPS_0.2V_80k_sin.bin",
        90e3:    "100MSPS_0.2V_90k_sin.bin",
    
        100e3:   "100MSPS_0.2V_100k_sin.bin",
        105e3:   "100MSPS_0.2V_105k_sin.bin",
        125e3:   "100MSPS_0.2V_125k_sin.bin",
        140e3:   "100MSPS_0.2V_140k_sin.bin",
        150e3:   "100MSPS_0.2V_150k_sin.bin",
        160e3:   "100MSPS_0.2V_160k_sin.bin",
        175e3:   "100MSPS_0.2V_175k_sin.bin",
        190e3:   "100MSPS_0.2V_190k_sin.bin",
        200e3:   "100MSPS_0.2V_200k_sin.bin",
        225e3:   "100MSPS_0.2V_225k_sin.bin",
        250e3:   "100MSPS_0.2V_250k_sin.bin",
        275e3:   "100MSPS_0.2V_275k_sin.bin",
    
        500e3:   "100MSPS_0.2V_500k_sin.bin",
        1e6:     "100MSPS_0.2V_1M_sin.bin",
        2e6:     "100MSPS_0.2V_2M_sin.bin",
        5e6:     "100MSPS_0.2V_5M_sin.bin",
        10e6:    "100MSPS_0.2V_10M_sin.bin",
        20e6:    "100MSPS_0.2V_20M_sin.bin",
    }

    captures = {
        frequency:
            load_capture(filename)

        for frequency, filename
        in files.items()
    }

    reference = load_capture(
        "100MSPS_0.2V_1M_sin.bin"
    )

    result = frequency_response(
        captures,
        reference
    )

    print("\nFREQUENCY RESPONSE")

    print(
        f"Reference gain = "
        f"{result['reference_gain']:.4f}"
    )

    if (
        result["bandwidth_3dB_Hz"]
        is not None
    ):
   
        print(
            f"-3 dB bandwidth = "
            f"{result['bandwidth_3dB_Hz'] / 1e6:.3f} MHz"
        )

    else:
        print(
            "-3 dB point not found"
        )

    for row in result["results"]:

        print(
            f"{row['frequency_Hz'] / 1e6:8.3f} MHz "
            f"{row['measured_peak_V']:.4f} V "
            f"{row['gain_dB']:+.2f} dB"
        )

    plot_frequency_response(
        result
    )
    
    plot_all_captures("100MSPS_*.bin")


if __name__ == "__main__":
    main()
