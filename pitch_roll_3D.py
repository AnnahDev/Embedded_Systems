import math
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# ----- CONFIG -----
PORT = 'COM10'  # Change to your port
BAUD = 115200
ser = serial.Serial(PORT, BAUD, timeout=1)

fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim([-2, 2])
ax.set_ylim([-2, 2])
ax.set_zlim([-2, 2])
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("3D Orientation Cube - Pitch & Roll")

# Cube vertices
cube_vertices = [
    [-1, -1, -0.2],  # 0
    [ 1, -1, -0.2],  # 1
    [ 1,  1, -0.2],  # 2
    [-1,  1, -0.2],  # 3
    [-1, -1,  0.2],  # 4
    [ 1, -1,  0.2],  # 5
    [ 1,  1,  0.2],  # 6
    [-1,  1,  0.2]   # 7
]

# Cube faces (indices into vertices)
faces = [
    [0,1,2,3],  # bottom
    [4,5,6,7],  # top
    [0,1,5,4],  # front
    [2,3,7,6],  # back
    [1,2,6,5],  # right
    [0,3,7,4]   # left
]

# Assign distinct colors to each face
face_colors = ["blue", "green", "red", "orange", "purple", "yellow"]

cube = Poly3DCollection(
    [[cube_vertices[v] for v in face] for face in faces],
    facecolors=face_colors,
    edgecolor="k",
    alpha=0.8
)
ax.add_collection3d(cube)

# Add coordinate axes for reference
ax.quiver(0, 0, 0, 2, 0, 0, color='r', arrow_length_ratio=0.1, linewidth=2)  # X-axis (red)
ax.quiver(0, 0, 0, 0, 2, 0, color='g', arrow_length_ratio=0.1, linewidth=2)  # Y-axis (green)
ax.quiver(0, 0, 0, 0, 0, 2, color='b', arrow_length_ratio=0.1, linewidth=2)  # Z-axis (blue)

# Add labels for axes
ax.text(2.2, 0, 0, "X (Roll)", color='r')
ax.text(0, 2.2, 0, "Y (Pitch)", color='g')
ax.text(0, 0, 2.2, "Z", color='b')

def rotation_matrix(pitch, roll):
    # convert to radians
    p = math.radians(pitch)
    r = math.radians(roll)

    # Roll = rotation around X-axis
    Rx = [
        [1, 0, 0],
        [0, math.cos(r), -math.sin(r)],
        [0, math.sin(r), math.cos(r)]
    ]
    # Pitch = rotation around Y-axis
    Ry = [
        [math.cos(p), 0, math.sin(p)],
        [0, 1, 0],
        [-math.sin(p), 0, math.cos(p)]
    ]

    # Combined: Ry * Rx
    R = [[sum(a*b for a,b in zip(R_row,X_col)) for X_col in zip(*Rx)] for R_row in Ry]
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
        if len(parts) != 2:
            return None, None
        pitch = float(parts[0])
        roll = float(parts[1])
        return pitch, roll
    except:
        return None, None

def update(frame):
    # Read serial data
    raw = ser.readline().decode(errors='ignore')
    if raw:
        pitch, roll = parse_line(raw)
        if pitch is not None and roll is not None:
            # Update cube orientation
            R = rotation_matrix(pitch, roll)
            rotated_vertices = apply_rotation(cube_vertices, R)
            new_faces = [[rotated_vertices[v] for v in face] for face in faces]
            cube.set_verts(new_faces)  # CORRECTED: set_verts instead of set_verts
            
            # Update title with current angles
            ax.set_title(f"3D Orientation - Pitch: {pitch:.1f}°, Roll: {roll:.1f}°")
    
    return cube,

# Initialize
def init():
    return cube,

ani = animation.FuncAnimation(fig, update, init_func=init, interval=30, blit=True)
plt.tight_layout()
plt.show()
ser.close()