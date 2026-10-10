from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import pickle


# ============================================================
# Settings
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "Data"
IMAGE_DIR = BASE_DIR.parent / "Images"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE_100MSPS = 100e6
SAMPLE_RATE_200MSPS = 200e6

ADC_ZERO_CODE = 127.076
VOLTS_PER_CODE = 0.009046051


# Current figure/axes
_current_fig = None
_current_ax = None


# ============================================================
# Plot data
# ============================================================

def plot(filename, sample_rate):

    global _current_fig, _current_ax

    path = Path(filename)

    if not path.is_absolute():
        path = DATA_DIR / path

    raw = np.fromfile(
        path,
        dtype=np.uint8
    )

    voltage = (
        raw.astype(np.float64)
        - ADC_ZERO_CODE
    ) * VOLTS_PER_CODE

    time_us = (
        np.arange(len(raw))
        / sample_rate
        * 1e6
    )

    _current_fig, _current_ax = plt.subplots()

    _current_ax.plot(
        time_us,
        voltage,
        linewidth=0.8
    )

    _current_ax.set_xlabel("Time (µs)")
    _current_ax.set_ylabel("Input Voltage (V)")
    _current_ax.grid(True)

    _current_fig.tight_layout()


# ============================================================
# Open saved FIG
# ============================================================

def open_fig(filename):
    """
    Open a .fig created by save_plot().
    """

    global _current_fig, _current_ax

    path = Path(filename)

    if not path.is_absolute():
        path = IMAGE_DIR / path

    with open(path, "rb") as f:
        _current_fig = pickle.load(f)

    if len(_current_fig.axes) == 0:
        raise ValueError(
            f"No axes found in {path}"
        )

    _current_ax = _current_fig.axes[0]

    print(f"Opened: {path}")

    return _current_fig


# ============================================================
# Axis limits
# ============================================================

def xlim(limits):

    if _current_ax is None:
        raise RuntimeError("No figure currently open.")

    _current_ax.set_xlim(
        limits[0],
        limits[1]
    )


def ylim(limits):

    if _current_ax is None:
        raise RuntimeError("No figure currently open.")

    _current_ax.set_ylim(
        limits[0],
        limits[1]
    )


# ============================================================
# Labels / title
# ============================================================

def title(text):

    if _current_ax is None:
        raise RuntimeError("No figure currently open.")

    _current_ax.set_title(text)


def xlabel(text):

    if _current_ax is None:
        raise RuntimeError("No figure currently open.")

    _current_ax.set_xlabel(text)


def ylabel(text):

    if _current_ax is None:
        raise RuntimeError("No figure currently open.")

    _current_ax.set_ylabel(text)


# ============================================================
# Save current plot
# ============================================================

def save_plot(name, frequency = 0):
    """
    Save current plot as:
        PNG
        PDF
        FIG
    """

    if _current_fig is None:
        raise RuntimeError("No figure currently open.")

    png_file = IMAGE_DIR / f"{name}.png"
    pdf_file = IMAGE_DIR / f"{name}.pdf"
    fig_file = IMAGE_DIR / f"{name}.fig"

    _current_fig.tight_layout()

    _current_fig.savefig(
        png_file,
        dpi=300,
        bbox_inches="tight"
    )

    _current_fig.savefig(
        pdf_file,
        bbox_inches="tight"
    )

    with open(fig_file, "wb") as f:
        pickle.dump(
            _current_fig,
            f,
            protocol=pickle.HIGHEST_PROTOCOL
        )

    print(f"Saved: {png_file}")
    print(f"Saved: {pdf_file}")
    print(f"Saved: {fig_file}")


# ============================================================
# Show / close
# ============================================================

def show():

    if _current_fig is None:
        raise RuntimeError("No figure currently open.")

    _current_fig.show()
    plt.show()


def close():

    global _current_fig, _current_ax

    if _current_fig is not None:
        plt.close(_current_fig)

    _current_fig = None
    _current_ax = None


plot("100MSPS_0.2V_5k_sin.bin", SAMPLE_RATE_100MSPS)
plt.title("Oscilloscope capture of 5kHz sine wave at 100MSPS")
plt.xlim(0, 600)
plt.ylim(-0.3, 0.3)
save_plot("Final_100MSPS_5k_sin", SAMPLE_RATE_100MSPS)
close()

plot("100MSPS_0.2V_100k_sin.bin", SAMPLE_RATE_100MSPS)
plt.title("Oscilloscope capture of 100kHz sine wave at 100MSPS")
plt.xlim(0, 10*5)
plt.ylim(-0.3, 0.3)
save_plot("Final_100MSPS_100k_sin", SAMPLE_RATE_100MSPS)
close()

plot("100MSPS_0.2V_10M_sin.bin", SAMPLE_RATE_100MSPS)
plt.title("Oscilloscope capture of 10MHz sine wave at 100MSPS")
plt.xlim(0, 0.5)
plt.ylim(-0.3, 0.3)
save_plot("Final_100MSPS_10M_sin", SAMPLE_RATE_100MSPS)
close()

plot("100MSPS_0.477V_1.1M_sin.bin", SAMPLE_RATE_100MSPS)
plt.title("Oscilloscope capture of 1.1MHz 0.477V sine wave at 100MSPS")
plt.xlim(0, 20)
plt.ylim(-0.8, 0.8)
save_plot("Final_100MSPS_0.477V_1.1M_sin", SAMPLE_RATE_100MSPS)
close()

plot("100MSPS_0.8V_1.1M_sin.bin", SAMPLE_RATE_100MSPS)
plt.title("Oscilloscope capture of 1.1MHz 0.8V sine wave at 100MSPS")
plt.xlim(0, 20)
plt.ylim(-1, 1)
save_plot("Final_100MSPS_0.8V_1.1M_sin", SAMPLE_RATE_100MSPS)
close()

plot("100MSPS_1.5V_1.1M_sin.bin", SAMPLE_RATE_100MSPS)
plt.title("Oscilloscope capture of 1.1MHz 1.5V sine wave at 100MSPS")
plt.xlim(0, 20)
plt.ylim(-2, 2)
save_plot("Final_100MSPS_1.5V_1.1M_sin", SAMPLE_RATE_100MSPS)
close()

plot("100MSPS_1V_1.1M_sin.bin", SAMPLE_RATE_100MSPS)
plt.title("Oscilloscope capture of 1.1MHz 1V sine wave at 100MSPS")
plt.xlim(0, 20)
plt.ylim(-2, 2)
save_plot("Final_100MSPS_1V_1.1M_sin", SAMPLE_RATE_100MSPS)
close()

plot("100MSPS_0.477V_1.1M_sin.bin", SAMPLE_RATE_100MSPS)
plt.title("Oscilloscope capture of 1.1MHz 0.477V sine wave at 100MSPS")
plt.xlim(0, 20)
plt.ylim(-0.8, 0.8)
save_plot("Final_100MSPS_0.477V_1.1M_sin", SAMPLE_RATE_100MSPS)
close()

open_fig("100MSPS_step_response.fig")
ax = plt.gca()
legend = ax.get_legend()
if legend is not None:
    legend.remove()
for line in list(ax.lines):
    label = line.get_label()
    if label == "50% instant":
        line.remove()
    elif label == "Settling band":
        line.remove()
    elif line.get_linestyle() == ":":
        line.remove()
plt.title("Step Response of 100MSPS Oscilloscope - Zoomed In")
plt.xlim(29, 50)
plt.ylim(-0.5, 0.1)
save_plot("Final_100MSPS_step_response_zoomed", SAMPLE_RATE_100MSPS)
close()


plot("100MSPS_0.2V_1M_square.bin", SAMPLE_RATE_100MSPS)
plt.title("Oscilloscope capture of 1MHz square wave at 100MSPS")
plt.xlim(50, 60)
plt.ylim(-0.4, 0.4)
save_plot("Final_100MSPS_1M_square_zoomed", SAMPLE_RATE_100MSPS)
close()


# 200MSPS
plot("200MSPS_0.2V_5k_sin.bin", SAMPLE_RATE_200MSPS)
plt.title("Oscilloscope capture of 5kHz sine wave at 200MSPS")
plt.xlim(0, 600)
plt.ylim(-0.3, 0.3)
save_plot("Final_200MSPS_5k_sin", SAMPLE_RATE_200MSPS)
close()

plot("200MSPS_0.2V_100k_sin.bin", SAMPLE_RATE_200MSPS)
plt.title("Oscilloscope capture of 100kHz sine wave at 200MSPS")
plt.xlim(0, 10*5)
plt.ylim(-0.3, 0.3)
save_plot("Final_200MSPS_100k_sin", SAMPLE_RATE_200MSPS)
close()

plot("200MSPS_0.2V_10M_sin.bin", SAMPLE_RATE_200MSPS)
plt.title("Oscilloscope capture of 10MHz sine wave at 200MSPS")
plt.xlim(0, 0.5)
plt.ylim(-0.3, 0.3)
save_plot("Final_200MSPS_10M_sin", SAMPLE_RATE_200MSPS)
close()

plot("200MSPS_0.477V_1.1M_sin.bin", SAMPLE_RATE_200MSPS)
plt.title("Oscilloscope capture of 1.1MHz 0.477V sine wave at 200MSPS")
plt.xlim(0, 5)
plt.ylim(-0.8, 0.8)
save_plot("Final_200MSPS_0.477V_1.1M_sin", SAMPLE_RATE_200MSPS)
close()

plot("200MSPS_0.8V_1.1M_sin.bin", SAMPLE_RATE_200MSPS)
plt.title("Oscilloscope capture of 1.1MHz 0.8V sine wave at 200MSPS")
plt.xlim(0, 5)
plt.ylim(-1, 1)
save_plot("Final_200MSPS_0.8V_1.1M_sin", SAMPLE_RATE_200MSPS)
close()

plot("200MSPS_1.5V_1.1M_sin.bin", SAMPLE_RATE_200MSPS)
plt.title("Oscilloscope capture of 1.1MHz 1.5V sine wave at 200MSPS")
plt.xlim(0, 5)
plt.ylim(-2, 2)
save_plot("Final_200MSPS_1.5V_1.1M_sin", SAMPLE_RATE_200MSPS)
close()

plot("200MSPS_1V_1.1M_sin.bin", SAMPLE_RATE_200MSPS)
plt.title("Oscilloscope capture of 1.1MHz 1V sine wave at 200MSPS")
plt.xlim(0, 5)
plt.ylim(-2, 2)
save_plot("Final_200MSPS_1V_1.1M_sin", SAMPLE_RATE_200MSPS)
close()

plot("200MSPS_0.477V_1.1M_sin.bin", SAMPLE_RATE_200MSPS)
plt.title("Oscilloscope capture of 1.1MHz 0.477V sine wave at 200MSPS")
plt.xlim(0, 20)
plt.ylim(-0.8, 0.8)
save_plot("Final_200MSPS_0.477V_1.1M_sin", SAMPLE_RATE_200MSPS)
close()

open_fig("200MSPS_step_response.fig")
ax = plt.gca()
legend = ax.get_legend()
if legend is not None:
    legend.remove()
for line in list(ax.lines):
    label = line.get_label()
    if label == "50% instant":
        line.remove()
    elif label == "Settling band":
        line.remove()
    elif line.get_linestyle() == ":":
        line.remove()
plt.title("Step Response of 200MSPS Oscilloscope - Zoomed In")
plt.xlim(0, 20)
plt.ylim(-0.5, 0.1)
save_plot("Final_200MSPS_step_response_zoomed", SAMPLE_RATE_200MSPS)
close()


plot("200MSPS_0.2V_1M_square.bin", SAMPLE_RATE_200MSPS)
plt.title("Oscilloscope capture of 1MHz square wave at 200MSPS")
plt.xlim(50, 55)
plt.ylim(-0.4, 0.4)
save_plot("Final_200MSPS_1M_square_zoomed", SAMPLE_RATE_200MSPS)
close()

plot("200MSPS_0.2V_1M_square.bin", SAMPLE_RATE_200MSPS)
plt.title("Oscilloscope capture of 1MHz square wave at 200MSPS")
plt.xlim(50, 55)
plt.ylim(-0.4, 0.4)
save_plot("Final_200MSPS_1M_square_zoomed", SAMPLE_RATE_200MSPS)
close()

