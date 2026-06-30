# Maya Python API 1.0

"""
test code ai generated for sticky lip exploration
"""

import maya.OpenMaya as om
import maya.cmds as cmds

# Example points (vertices) - list of (x, y, z)
points = [
    (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),  # bottom face
    (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)   # top face
]

# Example faces (connectivity by vertex indices)
faces = [
    [0, 1, 2, 3],  # bottom
    [4, 5, 6, 7],  # top
    [0, 1, 5, 4],  # side
    [1, 2, 6, 5],
    [2, 3, 7, 6],
    [3, 0, 4, 7]
]

# Convert points to MPointArray
mPoints = om.MPointArray()
for p in points:
    mPoints.append(om.MPoint(p[0], p[1], p[2]))

# Prepare polygon counts (vertices per face) and polygon connectivities (flattened indices)
polygonCounts = om.MIntArray()
polygonConnects = om.MIntArray()

for face in faces:
    polygonCounts.append(len(face))
    for idx in face:
        polygonConnects.append(idx)

# Create the mesh
meshFn = om.MFnMesh()
meshObject = meshFn.create(
    mPoints.length(),          # number of vertices
    len(faces),                # number of faces
    mPoints,                   # MPointArray of vertices
    polygonCounts,             # vertices per face
    polygonConnects            # flattened vertex indices
)

# Optional: name the mesh in Maya scene
meshName = cmds.rename(meshFn.name(), "meshFromAPI1")
print("Mesh created with name:", meshName)

# Example usage: simply modifying 'points' and 'faces' will create different shapes.