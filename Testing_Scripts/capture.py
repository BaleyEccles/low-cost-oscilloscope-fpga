from pathlib import Path
import serial
import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent
print(BASE_DIR)
OPENFPGALOADER = Path("/home/baley/UTAS/Honours/Methods/openFPGALoader/build/openFPGALoader")

BITSTREAM = Path.home() / "200MHz_Working.bit"

PORT = "/dev/ttyUSB1"
BAUD = 115200
NUM_SAMPLES = 65536

filename = sys.argv[1] if len(sys.argv) > 1 else "tmp.bin"
output_file = BASE_DIR / "../Data/" / filename


# ============================================================
# Check files
# ============================================================

if not OPENFPGALOADER.exists():
    print(f"ERROR: openFPGALoader not found: {OPENFPGALOADER}")
    sys.exit(1)

if not BITSTREAM.exists():
    print(f"ERROR: bitstream not found: {BITSTREAM}")
    sys.exit(1)


# ============================================================
# Open UART BEFORE programming FPGA
# ============================================================

print(f"Opening {PORT}...")

with serial.Serial(PORT, BAUD, timeout=2) as ser:

    # Remove any stale bytes from previous runs
    ser.reset_input_buffer()

    # ========================================================
    # Program FPGA
    # ========================================================

    print("Programming FPGA...")
    print(f"Bitstream: {BITSTREAM}")

    result = subprocess.run(
        [str(OPENFPGALOADER), str(BITSTREAM)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    print(result.stdout)

    if (
        result.returncode != 0
        or "Open file FAIL" in result.stdout
        or "Error:" in result.stdout
    ):
        print("FPGA programming failed.")
        sys.exit(1)

    print("FPGA programmed successfully.")

    # ========================================================
    # Receive ADC data
    # ========================================================

    data = bytearray()

    print(f"Receiving {NUM_SAMPLES} samples...")

    while len(data) < NUM_SAMPLES:

        chunk = ser.read(NUM_SAMPLES - len(data))

        if not chunk:
            print()
            print(f"Timed out after receiving " f"{len(data)}/{NUM_SAMPLES} bytes")
            break

        data.extend(chunk)

        print(
            f"\rReceived {len(data):5d}/{NUM_SAMPLES} "
            f"({100 * len(data) / NUM_SAMPLES:5.1f}%)",
            end="",
            flush=True,
        )


# ============================================================
# ALWAYS save what was received
# ============================================================

with open(output_file, "wb") as f:
    f.write(data)

print()
print(f"Saved {len(data)} bytes to:")
print(output_file)

if len(data) != NUM_SAMPLES:
    print(f"WARNING: capture incomplete " f"({NUM_SAMPLES - len(data)} bytes missing)")
else:
    print("Capture complete.")
