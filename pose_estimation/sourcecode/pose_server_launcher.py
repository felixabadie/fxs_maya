from PySide6 import QtWidgets
from maya import OpenMayaUI as omui
from shiboken6 import wrapInstance
import subprocess
import os

server_process = None
server_tool_window = None

def get_maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QMainWindow)

def start_server():
    global server_process 
    if server_process is not None:
        print("Server already running")
        return

    python_exe = r"D:\fa026_Bachelor\venv\Scripts\python.exe"
    server_script = os.path.join(os.path.dirname(__file__), "pose_server.py")
    subprocess.Popen(
        [python_exe, server_script], 
        creationflags=subprocess.CREATE_NEW_CONSOLE)
    print("PoseServer launched as subprocess.")

def stop_server():
    global server_process
    if server_process is None:
        print("No server running")
        return
    
    server_process.terminate()
    server_process = None


class serverTool(QtWidgets.QDialog):
    def __init__(self, parent = get_maya_main_window()):
        super().__init__(parent)
        self.setWindowTitle("Pose Server Manager")
        self.setLayout(QtWidgets.QVBoxLayout())

        btn_start_server = QtWidgets.QPushButton("Start Server")
        btn_stop_server = QtWidgets.QPushButton("Stop Server")
        btn_start_server.clicked.connect(start_server())
        btn_stop_server.clicked.connect(stop_server())

        self.layout().addWidget(btn_start_server)
        self.layout().addWidget(btn_stop_server)

def show_server_tool():
    global server_tool_window
    
    try:
        server_tool_window.close()
    except:
        pass

    server_tool_window = serverTool()
    server_tool_window.show()

if __name__ == "main":
    show_server_tool()