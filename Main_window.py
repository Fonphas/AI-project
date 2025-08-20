import sys
import cv2
from Main_Software import AI_Detection
from ultralytics import YOLO  
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
        self.camera_LH = None
        self.camera_RH = None
        self.timer_LH = QTimer(self)
        self.timer_RH = QTimer(self)

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
        self.label_5.setGeometry(QRect(30, 50, 161, 17))
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
        self.buttonBox.clicked.connect(self.connect_camera)

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

        # Start Button
        self.StartButton = QPushButton(self.centralwidget)
        self.StartButton.setGeometry(QRect(720, 370, 131, 25))
        self.StartButton.setIcon(QIcon.fromTheme("go-next"))

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
    
    def connect_camera(self):
        print("Select Mode Video")

        selected = self.comboBox.currentText()
    # LH = USB1
        self.frame_LH = cv2.VideoCapture(1)
        if self.frame_LH.isOpened():
            print("LH camera connected successfully.")
            self.timer_LH.timeout.connect(self.update_frame_LH)
            self.timer_LH.start(30)
    
        else:
            print("Failed to connect LH camera.")

    # RH = USB2
        self.frame_RH = cv2.VideoCapture(2)
        if self.frame_RH.isOpened():
            print("RH camera connected successfully.")
            self.timer_RH.timeout.connect(self.update_frame_RH)
            self.timer_RH.start(30)
        else:
            print("Failed to connect RH camera.")
            
        if selected == "VDO":
            print("Select video file")
            file_path, _ = QFileDialog.getOpenFileName(
            self, "Select video file", "", "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)"
            )

        if file_path:
           self.camera = cv2.VideoCapture(file_path)
           if self.camera.isOpened():
                print(f"Video file {file_path} opened successfully.")
           else:
                print("Failed to open selected video.")
                self.camera = None
            
        else:
            print("No file selected.")


    def display_frame(self, frame, label_widget):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg).scaled(
            label_widget.width(),
            label_widget.height(),
            Qt.KeepAspectRatio,
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
        self.StartButton.setText(_tr("MainWindow", "Start Detect"))
        self.menuYOLO_model.setTitle(_tr("MainWindow", "YOLO model"))
        self.menuSetting.setTitle(_tr("MainWindow", "Setting"))

    
#End of MainWindow class    
if __name__ == "__main__": 
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


























































