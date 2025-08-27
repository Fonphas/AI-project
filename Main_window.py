import sys
import cv2
from ultralytics import YOLO 
import torch
print("CUDA available:", torch.cuda.is_available())
print("CUDA device count:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("CUDA device name:", torch.cuda.get_device_name(0))
 
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QFileDialog, QComboBox, QLabel, QSlider,
    QSpinBox, QDialogButtonBox, QTableWidget, QTableWidgetItem, QPushButton,
    QMenuBar, QMenu, QStatusBar, QVBoxLayout
)
from PySide6.QtCore import Qt, QTimer, QRect, QCoreApplication, QMetaObject
from PySide6.QtGui import QIcon, QFont, QCursor, QAction, QPixmap, QImage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("AGC - Terminal direction Detection")

        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {self.device}")

        self.model = YOLO()  
        self.model.to(self.device)  # push model to GPU if available

        # Enable FP16 for faster inference (only works on CUDA)
        if self.device != 'cpu':
            self.model.model.half()
            print("Model running in FP16 mode on GPU")
        else:
            print("Model running in FP32 mode on CPU")



        self.camera_LH = None
        self.camera_RH = None
        self.timer_LH = QTimer(self)
        self.timer_RH = QTimer(self)
        self.cap_LH = None
        self.cap_RH = None

        

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("Main_Window")
        MainWindow.resize(950, 600)
        MainWindow.setCursor(QCursor(Qt.ArrowCursor))

        # Central widget (create first!)
        self.centralwidget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)

        # Camera ComboBox
        self.comboBox = QComboBox(self.centralwidget)
        icon_camera = QIcon.fromTheme("camera-web")
        self.comboBox.addItem(icon_camera, "")
        self.comboBox.addItem(icon_camera, "")
        self.comboBox.addItem("")
        self.comboBox.setGeometry(QRect(100, 375, 89, 25))

        # Camera Label 
        self.label = QLabel(self.centralwidget)
        self.label.setGeometry(QRect(30, 380, 67, 17))
        


        # Title Label
        #LH
        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setGeometry(QRect(30, 20, 161, 17))
        font = QFont()
        font.setPointSize(14)
        self.label_2.setFont(font)
        
        #RH
        self.label_5 = QLabel(self.centralwidget)
        self.label_5.setGeometry(QRect(445, 20, 161, 17))
        font = QFont()
        font.setPointSize(14)
        self.label_5.setFont(font)
        

        # Confidence Slider and Label
        self.horizontalSlider = QSlider(Qt.Horizontal, self.centralwidget)
        self.horizontalSlider.setGeometry(QRect(160, 410, 141, 31))
        self.horizontalSlider.setMaximum(100)
        self.horizontalSlider.setValue(50) 
        self.horizontalSlider.setTickPosition(QSlider.TicksBelow)

        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setGeometry(QRect(30, 415, 141, 16))

        # Confidence SpinBox
        self.spinBox = QSpinBox(self.centralwidget)
        self.spinBox.setGeometry(QRect(310, 410, 44, 26))
        self.spinBox.setMaximum(100)
        self.spinBox.setValue(50) 

        # Connecting the slider and spinbox
        self.horizontalSlider.valueChanged.connect(self.spinBox.setValue)
        self.spinBox.editingFinished.connect(lambda: self.horizontalSlider.setValue(self.spinBox.value()))

        # OK ButtonBox
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply, self.centralwidget)
        self.buttonBox.setGeometry(QRect(200, 375, 68, 25))
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.clicked.connect(self.connect_camera) # Connect to camera when clicked

        # Table Widget
        self.tableWidget = QTableWidget(self.centralwidget)
        self.tableWidget.setGeometry(QRect(480, 400, 411, 150))
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(["Date/Time", "Result", "%confidence"])
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setStretchLastSection(True)

        # Model ComboBox and Label
        self.comboBox_2 = QComboBox(self.centralwidget)
        self.comboBox_2.setGeometry(QRect(550, 370, 131, 25))
        self.comboBox_2.addItems(["", ""])

        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setGeometry(QRect(490, 370, 51, 21))

        # Menu bar and menus
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setGeometry(QRect(0, 0, 920, 22))
        MainWindow.setMenuBar(self.menubar)

        self.menuYOLO_model = QMenu(self.menubar)
        self.menuSetting = QMenu(self.menubar)
        self.menubar.addAction(self.menuYOLO_model.menuAction())
        self.menubar.addAction(self.menuSetting.menuAction())

        # Actions
        self.actionOpen = QAction(MainWindow)
        self.menuYOLO_model.addAction(self.actionOpen)
        self.actionOpen.triggered.connect(self.load_yolo_model)
        self.model = None

        # Status bar
        self.statusbar = QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)
        

        # Company Logo (make it a child of centralwidget)
        self.logo_label = QLabel(self.centralwidget)
        self.logo_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.logo_label.setGeometry(QRect(25, 440, 100, 100))
        pixmap = QPixmap("/home/orin_nano/project/Terminal wrong direction detection/AATH 50th Logo.png")
        
        #debug logo img
        if pixmap.isNull():
            print("Error: Logo image not found.")
        else:
            print("Logo image loaded successfully.")
        if not pixmap.isNull():
            self.logo_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))


        # Frame LH
        self.frame_LH = QFrame(self.centralwidget)
        self.frame_LH.setGeometry(QRect(30, 50, 410, 291))
        self.frame_LH.setFrameShape(QFrame.StyledPanel)
        self.frame_LH.setFrameShadow(QFrame.Raised)

        self.video_label_LH = QLabel(self.frame_LH)
        self.video_label_LH.setGeometry(QRect(0, 0, 431, 291))
        self.video_label_LH.setStyleSheet("background-color : black;")
        self.video_label_LH.setAlignment(Qt.AlignCenter)
        self.video_label_LH.setText("No video feed")

    def update_frame_LH(self):
        if self.cap_LH and self.cap_LH.isOpened():
            ret, frame = self.cap_LH.read()
            if ret:
                if self.comboBox.currentText() in ["USB1", "USB2"]:
                    frame = cv2.flip(frame, 1)  # Mirror for USB cameras
                    if self.model is not None:
                        results = self.model.predict(frame, imgsz=640, conf=0.5, verbose=False)
                        frame = results[0].plot()  # draw bboxes

                    self.display_frame(frame, self.video_label_LH)
            else:
                print("Failed to read frame.")
        else:
            print("Fail to read frame")
            if self.cap_LH:
                self.cap_LH.release()
        


    def connect_camera(self):
        selected = self.comboBox.currentText()
        print("Selected Camera:", selected)

        # Stop previous streams
        self.timer_LH.stop()
        if self.cap_LH and self.cap_LH.isOpened():
            self.cap_LH.release()
            self.cap_LH = None

        # Disconnect previous timer to avoid multiple connections
        #try:
         #   self.timer_LH.timeout.disconnect()
        #except Exception:
         #   pass

        # LH = USB1, USB2, or VDO
        if selected == "USB1":
            self.cap_LH = cv2.VideoCapture(1)
        elif selected == "USB2":
            self.cap_LH = cv2.VideoCapture(0)
        elif selected == "VDO":
            file_path, _ = QFileDialog.getOpenFileName()
        if file_path:
            print("Opening video file:", file_path)   # debug
            self.cap_LH = cv2.VideoCapture(file_path)
        else:
            print("No video file selected.")
            return
        

        if self.cap_LH and self.cap_LH.isOpened():
            print(f"{selected} connected successfully.")
            self.timer_LH.timeout.connect(self.update_file_video 
                                          if selected == "VDO" else self.update_frame_LH)
            
            self.timer_LH.start(30)
        else:
            print(f"Failed to connect {selected}.")

        # Frame RH
        self.frame_RH = QFrame(self.centralwidget)
        self.frame_RH.setGeometry(QRect(445, 50, 410, 291))
        self.frame_RH.setFrameShape(QFrame.StyledPanel)
        self.frame_RH.setFrameShadow(QFrame.Raised)

        self.video_label_RH = QLabel(self.frame_RH)
        self.video_label_RH.setGeometry(QRect(1, 0, 431, 291))
        self.video_label_RH.setStyleSheet("background-color : black;")
        self.video_label_RH.setAlignment(Qt.AlignCenter)
        self.video_label_RH.setText("No video feed")

        self.buttonBox.clicked.connect(self.connect_camera) #Start after click button
    
    def update_frame_RH(self):
        if self.cap_RH and self.cap_RH.isOpened():
            ret, frame = self.cap_RH.read()
            if ret:
                frame = cv2.flip(frame, 1)  #Mirror
                self.display_frame(frame, self.video_label_RH)
            else:
                print("Failed to read frame.")
    # RH = USB2
    def connect_camera_RH(self):
        selected = self.comboBox.currentText()
        print("Select Camera", selected)

        self.cap_RH = cv2.VideoCapture(0)
        if self.cap_RH.isOpened():
            print("RH camera connected successfully.")
            self.timer_RH.timeout.connect(self.update_frame_RH)
            self.timer_RH.start(30)
        else:
            print("Failed to connect RH camera.")

    def update_file_video(self):
        if self.cap_LH and self.cap_LH.isOpened():
            ret, frame = self.cap_LH.read()
            if ret:
                frame = cv2.flip(frame,1)  
                self.display_frame(frame, self.video_label_LH)
                
                if self.model is not None:
                    results = self.model.predict(frame, imgsz=640, conf=0.5, verbose=False)
                    frame = results[0].plot()  # draw bboxes
                    self.display_frame(frame, self.video_label_LH)
            else:
                print("Failed to read frame.")
                self.timer_LH.stop()
        else:
            print("Fail to read frame")


        print("Model device:", next(self.model.model.parameters()).device) #Check Device that's model running on
            
       
    def display_frame(self, frame, label_widget):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg).scaled(
        label_widget.size(),
        Qt.IgnoreAspectRatio,
        Qt.SmoothTransformation
    )
        label_widget.setPixmap(pixmap)

    def load_yolo_model(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select YOLO model", "", "Model Files (*.pt);;All Files (*)")
        if file_path:
            try:
                self.model= YOLO(file_path)
                print(f"Model loaded from {file_path}")
            except Exception as e:
                print(f"Error loading model: {e}")

    def retranslateUi(self, MainWindow):
        _tr = QCoreApplication.translate
        MainWindow.setWindowTitle(_tr("MainWindow", "Main window"))
        self.actionOpen.setText(_tr("MainWindow", "Load model..."))
        self.comboBox.setItemText(0, _tr("MainWindow", "USB1"))
        self.comboBox.setItemText(1, _tr("MainWindow", "USB2"))
        self.comboBox.setItemText(2, _tr("MainWindow", "VDO"))
        self.label.setText(_tr("MainWindow", "Camera :"))
        self.label_2.setText(_tr("MainWindow", "Terminal LH"))
        self.label_5.setText(_tr("MainWindow", "Terminal RH"))
        self.label_3.setText(_tr("MainWindow", "%Confident ratio : "))
        self.comboBox_2.setItemText(0, _tr("MainWindow", "640A-R"))
        self.comboBox_2.setItemText(1, _tr("MainWindow", "..."))
        self.label_4.setText(_tr("MainWindow", "Model :"))
        self.menuYOLO_model.setTitle(_tr("MainWindow", "YOLO model"))
        self.menuSetting.setTitle(_tr("MainWindow", "Setting"))

    
#End of MainWindow class    
if __name__ == "__main__": 
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


























































