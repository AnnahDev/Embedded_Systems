import sys 
import math
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle
from collections import deque

# ----- CONFIG -----
PORT = 'COM3'  # <- change if needed
BAUD = 115200
WINDOW = 200                   # number of samples shown

ser = serial.Serial(PORT, BAUD, timeout=1)

pitch_buf = deque(maxlen=WINDOW)
x_idx     = deque(maxlen=WINDOW)

fig = plt.figure(figsize=(9,5))

# Top: time-series lines (pitch only)
ax1 = fig.add_subplot(2,1,1)
(line_pitch,) = ax1.plot([], [], label="Pitch (°)")
ax1.set_xlim(0, WINDOW)
ax1.set_ylim(-90, 90)
ax1.set_xlabel("Samples")
ax1.set_ylabel("Angle (°)")
ax1.set_title("MPU6050 Pitch (Y) Only")
ax1.legend(loc="upper right")

# Bottom: "seesaw" driven by Pitch
ax2 = fig.add_subplot(2,1,2)
ax2.set_xlim(-2, 2)
ax2.set_ylim(-1.2, 1.2)
ax2.set_aspect('equal', adjustable='box')
ax2.set_xticks([])
ax2.set_yticks([])
ax2.set_title("Pitch-driven Tilt")

bar = Rectangle((-1.5, -0.1), 3.0, 0.2, angle=0)
ax2.add_patch(bar)

def update_bar_angle(angle_deg):
    t = plt.matplotlib.transforms.Affine2D() \
        .rotate_deg_around(0, 0, angle_deg) + ax2.transData
    bar.set_transform(t)

def parse_line(line):
    try:
        parts = line.strip().split(',')
        if len(parts) < 1:
            return None
        pitch = float(parts[0])
        return pitch
    except:
        return None

def init():
    line_pitch.set_data([], [])
    update_bar_angle(0)
    return (line_pitch, bar)

def update(frame):
    for _ in range(5):
        raw = ser.readline().decode(errors='ignore')
        if not raw:
            break
        pitch = parse_line(raw)
        if pitch is None:
            continue
        pitch_buf.append(pitch)
        x_idx.append(len(x_idx) + 1 if x_idx else 1)

    xs = list(range(len(x_idx)))
    line_pitch.set_data(xs, list(pitch_buf))
    ax1.set_xlim(max(0, len(xs)-WINDOW), max(WINDOW, len(xs)))
    if pitch_buf:
        update_bar_angle(pitch_buf[-1])

    return (line_pitch, bar)

ani = animation.FuncAnimation(fig, update, init_func=init, interval=30, blit=True)
plt.tight_layout()
plt.show()
