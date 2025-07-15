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
        #self.detector = AI_Detection()  
        self.camera = None
        self.timer = QTimer(self)

        self.startButton.clicked.connect(self.connect_camera) #Start after click button

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("Main_Window")
        MainWindow.resize(950, 600)
        MainWindow.setCursor(QCursor(Qt.ArrowCursor))

        # Central widget
        self.centralwidget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)

        # Company Logo (make it a child of centralwidget)
        self.logo_label = QLabel(self.centralwidget)
        self.logo_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.logo_label.setGeometry(QRect(800, 20, 100, 100))
        pixmap = QPixmap("/home/orin_nano/project/Terminal wrong direction detection/AATH 50th Logo.png")
        
        #debug logo img
        if pixmap.isNull():
            print("Error: Logo image not found.")
        else:
            print("Logo image loaded successfully.")
        if not pixmap.isNull():
            self.logo_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        # Frame
        self.frame = QFrame(self.centralwidget)
        self.frame.setGeometry(QRect(30, 50, 431, 291))
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
    
        self.video.label = QLabel(self.frame)
        self.video.label.setGeometry(QRect(0, 0, 431, 291))
        self.video.label.setStyleSheet("background-color : black;")
        self.video.label.setAlignment(Qt.AlignCenter)
        self.video.label.setText("No video feed")
    
    def update_frame(self):
        if self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                Q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(Q_image).scaled(
                        self.video.label.width(),
                        self.video.label.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                )
                self.video.label.setPixmap(pixmap)


        # Camera ComboBox
        self.comboBox = QComboBox(self.centralwidget)
        icon_camera = QIcon.fromTheme("camera-web")
        self.comboBox.addItem(icon_camera, "")
        self.comboBox.addItem(icon_camera, "")
        self.comboBox.addItem("")
        self.comboBox.setGeometry(QRect(100, 350, 89, 25))

        # Camera Label
        self.label = QLabel(self.centralwidget)
        self.label.setGeometry(QRect(30, 352, 67, 17))

        # Title Label
        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setGeometry(QRect(30, 20, 161, 17))
        font = QFont()
        font.setPointSize(14)
        self.label_2.setFont(font)

        # Confidence Slider and Label
        self.horizontalSlider = QSlider(Qt.Horizontal, self.centralwidget)
        self.horizontalSlider.setGeometry(QRect(160, 388, 141, 31))
        self.horizontalSlider.setMaximum(100)
        self.horizontalSlider.setValue(50) 
        self.horizontalSlider.setTickPosition(QSlider.TicksBelow)

        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setGeometry(QRect(30, 390, 141, 16))

        # Confidence SpinBox
        self.spinBox = QSpinBox(self.centralwidget)
        self.spinBox.setGeometry(QRect(310, 390, 44, 26))
        self.spinBox.setMaximum(100)
        self.spinBox.setValue(50) 

        # Connecting the slider and spinbox
        self.horizontalSlider.valueChanged.connect(self.spinBox.setValue)
        self.spinBox.editingFinished.connect(lambda: self.horizontalSlider.setValue(self.spinBox.value()))

        # OK ButtonBox
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply, self.centralwidget)
        self.buttonBox.setGeometry(QRect(200, 350, 61, 25))
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.accepted.connect(self.connect_camera)

        # Table Widget
        self.tableWidget = QTableWidget(self.centralwidget)
        self.tableWidget.setGeometry(QRect(480, 250, 411, 251))
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(["Date/Time", "Result", "%confidence"])
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setStretchLastSection(True)

        # Model ComboBox and Label
        self.comboBox_2 = QComboBox(self.centralwidget)
        self.comboBox_2.setGeometry(QRect(550, 210, 131, 25))
        self.comboBox_2.addItems(["", ""])

        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setGeometry(QRect(490, 210, 51, 21))

        # Start Button
        self.StartButton = QPushButton(self.centralwidget)
        self.StartButton.setGeometry(QRect(720, 210, 131, 25))
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

    def load_yolo_model(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select YOLO model", "", "Model Files (*.pt);;All Files (*)")
        if file_path:
            try:
                self.detector.load_model(file_path)
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
        self.label_3.setText(_tr("MainWindow", "%Confident ratio : "))
        self.comboBox_2.setItemText(0, _tr("MainWindow", "640A-R"))
        self.comboBox_2.setItemText(1, _tr("MainWindow", "..."))
        self.label_4.setText(_tr("MainWindow", "Model :"))
        self.StartButton.setText(_tr("MainWindow", "Start Detect"))
        self.menuYOLO_model.setTitle(_tr("MainWindow", "YOLO model"))
        self.menuSetting.setTitle(_tr("MainWindow", "Setting"))

    def connect_camera(self):
        print("Select Mode Video")
        selected = self.comboBox.currentText()
    
        if selected == "USB1":
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                print("USB1 camera connected successfully.")
            else :
                print("Failed to connect to USB1 camera.")
                

        elif selected == "USB2":
            self.camera = cv2.VideoCapture(1)
            if self.camera.isOpened():
                print("USB2 camera connected successfully.")
            else :
                print("Failed to connect to USB2 camera.")

        elif selected == "VDO":
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
        
   
            
    
        
#End of MainWindow class    
if __name__ == "__main__": 
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


























































