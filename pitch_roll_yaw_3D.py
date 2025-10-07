import sys
import math
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import pitch_2D

# ----- CONFIG -----
PORT = 'COM10'   # adjust if needed
BAUD = 115200
WINDOW = 200   # number of samples shown

ser = serial.Serial(PORT, BAUD, timeout=1)

pitch_buf = deque(maxlen=WINDOW)
roll_buf  = deque(maxlen=WINDOW)
yaw_buf   = deque(maxlen=WINDOW)
x_idx     = deque(maxlen=WINDOW)

fig = plt.figure(figsize=(9,5))

# Top: time-series lines
ax1 = fig.add_subplot(2,1,1)
(line_pitch,) = ax1.plot([], [], label="Pitch (°)")
(line_roll,)  = ax1.plot([], [], label="Roll (°)")
(line_yaw,)   = ax1.plot([], [], label="Yaw (°)")
ax1.set_xlim(0, WINDOW)
ax1.set_ylim(-180, 180)
ax1.set_xlabel("Samples")
ax1.set_ylabel("Angle (°)")
ax1.set_title("MPU6050 Pitch (Y), Roll (X), Yaw (Z)")
ax1.legend(loc="upper right")

# Bottom: 3D orientation cube
ax2 = fig.add_subplot(2,1,2, projection='3d')
ax2.set_xlim([-2, 2])
ax2.set_ylim([-2, 2])
ax2.set_zlim([-2, 2])
ax2.set_title("3D Orientation (Pitch, Roll, Yaw)")

# Cube vertices
cube_vertices = [
    [-1, -1, -1],
    [ 1, -1, -1],
    [ 1,  1, -1],
    [-1,  1, -1],
    [-1, -1,  1],
    [ 1, -1,  1],
    [ 1,  1,  1],
    [-1,  1,  1]
]

# Cube faces
faces = [
    [0,1,2,3],  # bottom
    [4,5,6,7],  # top
    [0,1,5,4],  # front
    [2,3,7,6],  # back
    [1,2,6,5],  # right
    [0,3,7,4]   # left
]

# Distinct colors for each face
face_colors = ["blue", "green", "red", "orange", "purple", "yellow"]

cube = Poly3DCollection(
    [[cube_vertices[v] for v in face] for face in faces],
    facecolors=face_colors,
    edgecolor="k",
    alpha=0.8
)
ax2.add_collection3d(cube)

# --- Rotation ---
def rotation_matrix(pitch, roll, yaw):
    p = math.radians(pitch)
    r = math.radians(roll)
    y = math.radians(yaw)

    Rx = [
        [1, 0, 0],
        [0, math.cos(r), -math.sin(r)],
        [0, math.sin(r),  math.cos(r)]
    ]
    Ry = [
        [ math.cos(p), 0, math.sin(p)],
        [0, 1, 0],
        [-math.sin(p), 0, math.cos(p)]
    ]
    Rz = [
        [math.cos(y), -math.sin(y), 0],
        [math.sin(y),  math.cos(y), 0],
        [0, 0, 1]
    ]

    # Order: Yaw * Pitch * Roll
    R1 = [[sum(a*b for a,b in zip(Rz_row,Rx_col)) for Rx_col in zip(*Rx)] for Rz_row in Rz]
    R = [[sum(a*b for a,b in zip(R1_row,Ry_col)) for Ry_col in zip(*Ry)] for R1_row in R1]
    return R

def apply_rotation(verts, R):
    rotated = []
    for v in verts:
        x,y,z = v
        rx = R[0][0]*x + R[0][1]*y + R[0][2]*z
        ry = R[1][0]*x + R[1][1]*y + R[1][2]*z
        rz = R[2][0]*x + R[2][1]*y + R[2][2]*z
        rotated.append([rx, ry, rz])
    return rotated

def parse_line(line):
    try:
        parts = line.strip().split(',')
        if len(parts) != 3:
            return None, None, None
        pitch = float(parts[0])
        roll  = float(parts[1])
        yaw   = float(parts[2])
        return pitch, roll, yaw
    except:
        return None, None, None

def init():
    line_pitch.set_data([], [])
    line_roll.set_data([], [])
    line_yaw.set_data([], [])
    return (line_pitch, line_roll, line_yaw, cube)

def update(frame):
    for _ in range(5):
        raw = ser.readline().decode(errors='ignore')
        if not raw:
            break
        pitch, roll, yaw = parse_line(raw)
        if pitch is None:
            continue
        pitch_buf.append(pitch)
        roll_buf.append(roll)
        yaw_buf.append(yaw)
        x_idx.append(len(x_idx) + 1 if x_idx else 1)

    # update time-series
    xs = list(range(len(x_idx)))
    line_pitch.set_data(xs, list(pitch_buf))
    line_roll.set_data(xs, list(roll_buf))
    line_yaw.set_data(xs, list(yaw_buf))
    ax1.set_xlim(max(0, len(xs)-WINDOW), max(WINDOW, len(xs)))

    # update cube
    if pitch_buf and roll_buf and yaw_buf:
        R = rotation_matrix(pitch_buf[-1], roll_buf[-1], yaw_buf[-1])
        rotated_vertices = apply_rotation(cube_vertices, R)
        new_faces = [[rotated_vertices[v] for v in face] for face in faces]
        cube.set_verts(new_faces)

    return (line_pitch, line_roll, line_yaw, cube)

ani = animation.FuncAnimation(fig, update, init_func=init, interval=30, blit=False)
plt.tight_layout()
plt.show()
ser.close()
File: pitch_2D.py