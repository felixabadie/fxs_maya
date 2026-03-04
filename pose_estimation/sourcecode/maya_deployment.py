from PySide6 import QtWidgets, QtGui, QtCore
from maya import OpenMayaUI as omui
from shiboken6 import wrapInstance
from pathlib import Path
from maya import cmds
import traceback
import requests
import shutil
import time
import os

draw_to_image_folder = Path(r"D:\fa026_Bachelor\draw_to_folder")
#drawing_export_dir = Path(r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\draw_to_folder\drawing_01")

joint_rotation_ranges = {
    "root_jnt": [(-15, 15), (0, 0), (-15, 15)],
    "spine_01_jnt": [(-10, 10), (0, 0), (-10, 10)],
    "spine_02_jnt": [(-10, 10), (0, 0), (-10, 10)],
    "spine_03_jnt": [(-10, 10), (0, 0), (-10, 10)],
    "neck_jnt": [(-10, 10), (-10, 10), (-10, 10)],
    "l_clavicle_jnt": [(0, 0), (-70, 0), (0, 0)],
    "l_shoulder_jnt": [(0, 0), (-65, 0), (0, 0)],
    "l_ellbow_jnt": [(0, 0), (0, 0), (-110, 110)],
    "r_clavicle_jnt": [(0, 0), (-70, 0), (0, 0)],
    "r_shoulder_jnt": [(0, 0), (-65, 0), (0, 0)],
    "r_ellbow_jnt": [(0, 0), (0, 0), (-110, 110)],
    "l_leg_jnt": [(-65, 65), (0, 20), (-50, 90)],
    "l_knee_jnt": [(0, 0), (0, 90), (0, 0)],
    "r_leg_jnt": [(-65, 65), (0, 20), (-50, 90)],
    "r_knee_jnt": [(0, 0), (0, 90), (0, 0)],
}


[[0.0, 55.66752624511719, 0.0], [0.0, 0.0, 0.0]]

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def get_joint_chain_from_dict(rotation_dict):
    """
    Instead of rig traversal joints are taken out of joint_rotation_ranges
    """
    joints = []
    missing = []
    for name in rotation_dict.keys():
        if cmds.objExists(name):
            joints.append(name)
        else:
            missing.append(name) 
    if missing:
        print(f"Felhlende Joints im Rig: {missing}")
    print("get_joint_chain_from_dict executed")
    return joints

            
joint_chain = get_joint_chain_from_dict(joint_rotation_ranges)
print(f"Joint Chain: {joint_chain}")


def get_maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QMainWindow)

def apply_rotation(predictions):

    try:

        for joint, rot in zip(joint_chain, predictions):
            print(f"Joint: {joint}, Rotation: {rot}")
            cmds.setAttr(f"{joint}.rotate", *rot)
            frame = cmds.currentTime(query=True)
            cmds.setKeyframe(joint_chain, t=frame)
            #print("entered appyly rotation for loop")
            print(f"{cmds.getAttr(f'{joint}.rotate')}")
    except Exception:
        print("cannot apply rotation")
        traceback.print_exc()

def export_images(image_export_dir, drawing, prediction):
    shutil.copy2(drawing, image_export_dir)
    shutil.copy2(prediction, image_export_dir)

#Send to Server
def predict_from_maya(image_path):

    """sends image to local server via post and receives json response"""

    url = "http://localhost:8000/"
    global start_time
    start_time = time.time()
    try:
        with open(image_path, "rb") as f:
            response = requests.post(url, files={"file": f})
    
        if response.status_code == 200:
            data = response.json()



            print("Server Time in seconds: ", data["duration"])
            if "rotations" in data:
                return data["rotations"]

            else:
                print("Server Antwort enthält keine 'rotations'")
                return None
            
    except requests.exceptions.ConnectionError:
        print(f"Server-Fehler ({response.status_code}): {response.text}")
        return None
    except requests.exceptions.Timeout:
        print("Server-Anfrage zu langsam (Timeout)")
        return None
    except Exception as e:
        print(f"Unbekannter Fehler: {e}")
        return None
    

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


class PaintWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(1024, 1024)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)


        self.eraser_mode = False
        self.background_color = QtCore.Qt.black
        self.pen_color = QtGui.QColor(255, 255, 255)  # Standard: Weiß
        self.pen_width = 2  # Standarddicke

        # Puffer, auf dem gezeichnet wird
        self.canvas = QtGui.QPixmap(self.size())
        self.canvas.fill(QtCore.Qt.black)

        self.last_pos = None

    def set_pen_color(self, color):
        self.pen_color = color

    def set_pen_width(self, width):
        self.pen_width = width

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.canvas)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_E:
            self.eraser_mode = not self.eraser_mode
            print(f"Eraser mode: {'ON' if self.eraser_mode else 'OFF'}")
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.eraser_mode = not self.eraser_mode
        elif event.button() == QtCore.Qt.LeftButton:
            self.last_pos = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton and self.last_pos is not None:
            painter = QtGui.QPainter(self.canvas)

            if self.eraser_mode:
                pen = QtGui.QPen(self.background_color, self.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap)
            else:
                pen = QtGui.QPen(self.pen_color, self.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap)
            
            painter.setPen(pen)
            current_pos = event.position().toPoint()
            painter.drawLine(self.last_pos, current_pos)
            painter.end()

            self.last_pos = current_pos
            self.update()

    def mouseReleaseEvent(self, event):
        self.last_pos = None

    def clear(self):
        self.canvas.fill(QtCore.Qt.black)
        self.update()

    def send_to_server(self):

        """executes predict_from_maya and later apply_rotation"""

        ensure_dir(draw_to_image_folder)
        image_path = os.path.join(draw_to_image_folder, "drawing.jpg")
        if self.canvas.save(image_path, "JPG"):
            print(f"Bild gespeichert unter: {image_path}")
            
            rotations = predict_from_maya(image_path)
            print(f"Rotations from server: {rotations}")
            if rotations:
                print(f"Vorhersage erhalten: {len(rotations)} Joints")
                apply_rotation(rotations)
                duration = time.time() - start_time
                print("Rotationen auf Rig angewendet")
                print("Vergangene Zeit in Maya: ", duration)

                cmds.refresh(force=True)
                
            else:
                print("Keine gültige Antwort vom Server.")
                
        else:
            print("Fehler beim Speichern des Bildes.")


class PaintTool(QtWidgets.QDialog):
    def __init__(self, parent=get_maya_main_window()):
        super().__init__(parent)
        self.setWindowTitle("Maya Paint Tool")
        self.setLayout(QtWidgets.QVBoxLayout())

        self.canvas = PaintWidget()
        self.layout().addWidget(self.canvas)

        color_layout = QtWidgets.QHBoxLayout()
        custom_colors = [
            (255, 18, 0),      # l_arm (rot)
            (250, 0, 214),     # head (pink)
            (255, 255, 255),   # Torso (fast weiß)
            (0, 233, 224),     # r_leg (cyan)
            (0, 217, 0),       # r_feet (grün)
            (23, 0, 255),      # r_arm (blau)
            (255, 155, 0),     # l_leg (orange)
            (248, 241, 1),     # l_feet (gelb)
        ]

        for r, g, b in custom_colors:
            color = QtGui.QColor(r, g, b)
            color_layout.addWidget(self.create_color_button(color))

        self.layout().addLayout(color_layout)

        thickness_layout = QtWidgets.QHBoxLayout()
        thickness_label = QtWidgets.QLabel("Strichdicke:")
        thickness_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        thickness_slider.setRange(1, 20)
        thickness_slider.setValue(self.canvas.pen_width)
        thickness_slider.valueChanged.connect(self.canvas.set_pen_width)
        thickness_layout.addWidget(thickness_label)
        thickness_layout.addWidget(thickness_slider)
        self.layout().addLayout(thickness_layout)

        self.layout().addLayout(thickness_layout)

        btn_clear = QtWidgets.QPushButton("Clear")
        btn_send = QtWidgets.QPushButton("Execute")
        btn_clear.clicked.connect(self.canvas.clear)
        btn_send.clicked.connect(self.canvas.send_to_server)
        self.layout().addWidget(btn_clear)
        self.layout().addWidget(btn_send)

    def create_color_button(self, color):
        btn = QtWidgets.QPushButton()
        btn.setFixedSize(20, 20)
        btn.setStyleSheet(f"background-color: {color.name()};")
        btn.clicked.connect(lambda: self.canvas.set_pen_color(color))
        return btn

def show_paint_tool():
    global paint_tool_window
    try:
        paint_tool_window.close()
        paint_tool_window.deleteLater()
    except:
        pass

    paint_tool_window = PaintTool()
    paint_tool_window.show()

if __name__ == "__main__":
    show_paint_tool()