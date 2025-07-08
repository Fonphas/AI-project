import sys
import cv2
from ultralytics import YOLO  
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QLabel,
    QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QSpinBox, QStatusBar, QMenuBar, QMenu
)
from PySide6.QtCore import Qt, QRect, QTimer
from PySide6.QtGui import QAction, QFont, QPalette, QColor, QImage, QPixmap


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AGC - Terminal Direction Detection")
        self.resize(1100, 651)

        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)

        self.cap_rh = None
        self.cap_lh = None
        self.timer = QTimer(self)

        self.setup_actions()
        self.setup_ui_elements()
        self.setup_menu()

    def setup_ui_elements(self):
        self.pushButton = self.create_button(self.centralwidget, "Detect", QRect(880, 150, 101, 41))
        self.pushButton.clicked.connect(self.start_detection)

        self.label = self.create_label(self.centralwidget, "Confidence ratio", QRect(30, 518, 111, 16))

        self.comboBox = self.create_combobox(self.centralwidget, QRect(30, 380, 101, 24), ["","Open file", "Camera 1", "Camera 2"])
        self.comboBox_2 = self.create_combobox(self.centralwidget, QRect(140, 380, 101, 24), ["","Open file", "Camera 1", "Camera 2"])

        self.label_2 = self.create_label(self.centralwidget, "LH", QRect(40, 360, 49, 16))
        self.label_3 = self.create_label(self.centralwidget, "RH", QRect(150, 360, 49, 16))

        self.tableWidget = self.create_table(self.centralwidget, QRect(30, 410, 331, 81), ["Product", "Status", "Detection"])
        self.tableWidget.setColumnWidth(0, 100)
        self.tableWidget.setColumnWidth(1, 100)
        self.tableWidget.setColumnWidth(2, 130)

        self.tableWidget_2 = QTableWidget(self.centralwidget)
        self.tableWidget_2.setGeometry(QRect(880, 70, 191, 71))
        self.tableWidget_2.setRowCount(2)
        self.tableWidget_2.setVerticalHeaderLabels(["Judgement", "Confident %"])
        self.tableWidget_2.setRowHeight(0, 35)
        self.tableWidget_2.setRowHeight(1, 35)

        self.pushButton_2 = self.create_button(self.centralwidget, "Connect", QRect(250, 380, 75, 24))
        self.pushButton_2.clicked.connect(self.connect_camera)

        self.tableWidget_3 = self.create_table(self.centralwidget, QRect(400, 340, 471, 251), ["No.", "Date/Time", "Class name"])
        self.tableWidget_3.setColumnWidth(0, 50)
        self.tableWidget_3.setColumnWidth(1, 200)
        self.tableWidget_3.setColumnWidth(2, 220)

        self.spinBox = QSpinBox(self.centralwidget)
        self.spinBox.setGeometry(QRect(140, 510, 61, 31))

        self.video_label_RH = self.create_labeled_widget("LH", QRect(40, 50, 49, 16), QRect(40, 70, 390, 251))
        self.video_label_LH = self.create_labeled_widget("RH", QRect(460, 50, 49, 16), QRect(460, 70, 390, 251))

        self.timer.timeout.connect(self.update_frame)

    def setup_actions(self):
        self.actionLoad_YOLO_model = QAction("Load YOLO model", self)
        self.actionLoad_YOLO_model.triggered.connect(self.load_yolo_model)
        self.model = None

    def load_yolo_model(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select YOLO Model File", "", "Model Files (*.pt);;All Files (*)"
        )
        if file_path:
            try:
                self.model = YOLO(file_path)
                print(f"YOLO model loaded: {file_path}")
            except Exception as e:
                print(f"Failed to load model: {e}")


    def setup_menu(self):
        self.menubar = QMenuBar(self)
        self.setMenuBar(self.menubar)

        self.menuModel_setting = QMenu("Model setting", self)
        self.menuModel_Load = QMenu("Model Load", self)

        self.menubar.addMenu(self.menuModel_setting)
        self.menubar.addMenu(self.menuModel_Load)

        self.menuModel_setting.addAction(self.actionLoad_YOLO_model)
        self.setStatusBar(QStatusBar(self))

    def create_button(self, parent, text, geometry):
        btn = QPushButton(text, parent)
        btn.setGeometry(geometry)
        self.apply_text_color(btn)
        return btn

    def create_label(self, parent, text, geometry):
        lbl = QLabel(text, parent)
        lbl.setGeometry(geometry)
        self.apply_text_color(lbl)
        return lbl

    def create_combobox(self, parent, geometry, items):
        box = QComboBox(parent)
        box.setGeometry(geometry)
        box.addItems(items)
        self.apply_text_color(box)
        return box

    def create_table(self, parent, geometry, headers):
        table = QTableWidget(parent)
        table.setGeometry(geometry)
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStyleSheet("color: rgb(0, 0, 127); font-weight: bold;")
        table.verticalHeader().setStyleSheet("color: rgb(0, 0, 127); font-weight: bold;")
        return table

    def create_labeled_widget(self, text, label_rect, widget_rect):
        self.create_label(self.centralwidget, text, label_rect)
        label = QLabel(self.centralwidget)
        label.setGeometry(widget_rect)
        label.setStyleSheet("background-color: black;")
        return label

    def apply_text_color(self, widget):
        palette = widget.palette()
        palette.setColor(QPalette.WindowText, QColor(0, 0, 127))
        widget.setPalette(palette)

    def connect_camera(self):
        rh_text = self.comboBox.currentText()
        lh_text = self.comboBox_2.currentText()

        if rh_text in ["Camera 1", "Camera 2"]:
            rh_index = 0 if rh_text == "Camera 1" else 1
            self.cap_rh = cv2.VideoCapture(rh_index)
            if not self.cap_rh.isOpened():
                print("Failed to open RH camera.")
                self.cap_rh = None
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select video file for RH", "Open file", "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)"
            )
            if file_path:
                self.cap_rh = cv2.VideoCapture(file_path)
                if not self.cap_rh.isOpened():
                    print("Failed to open selected RH video.")
                    self.cap_rh = None

        if lh_text in ["Camera 1", "Camera 2"]:
            lh_index = 0 if lh_text == "Camera 1" else 1
            if self.cap_rh and lh_index == (0 if rh_text == "Camera 1" else 1):
                print("RH and LH cannot use the same camera index.")
                self.cap_lh = None
            else:
                self.cap_lh = cv2.VideoCapture(lh_index)
                if not self.cap_lh.isOpened():
                    print("Failed to open LH camera.")
                    self.cap_lh = None
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select video file for LH", "Open file", "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)"
            )
            if file_path:
                self.cap_lh = cv2.VideoCapture(file_path)
                if not self.cap_lh.isOpened():
                    print("Failed to open selected LH video.")
                    self.cap_lh = None

        if (self.cap_rh and self.cap_rh.isOpened()) or (self.cap_lh and self.cap_lh.isOpened()):
            self.timer.start(30)
        else:
            print("Failed to open any video/camera.")

    def update_frame(self):
        if self.cap_rh and self.cap_rh.isOpened():
            ret_rh, frame_rh = self.cap_rh.read()
            if ret_rh:
                frame_rgb_rh = cv2.cvtColor(frame_rh, cv2.COLOR_BGR2RGB)
                if self.model:
                    results = self.model(frame_rgb_rh, verbose=False)[0]
                    for box in results.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cls = int(box.cls[0])
                        label = self.model.names[cls]
                        conf = box.conf[0].item()
                        cv2.rectangle(frame_rgb_rh, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame_rgb_rh, f"{label} {conf:.2f}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

                image_rh = QImage(frame_rgb_rh.data, frame_rgb_rh.shape[1], frame_rgb_rh.shape[0], QImage.Format_RGB888)
                pixmap_rh = self.crop_and_scale(image_rh, self.video_label_RH.width(), self.video_label_RH.height())
                self.video_label_RH.setPixmap(pixmap_rh)

        if self.cap_lh and self.cap_lh.isOpened():
            ret_lh, frame_lh = self.cap_lh.read()
            if ret_lh:
                frame_rgb_lh = cv2.cvtColor(frame_lh, cv2.COLOR_BGR2RGB)
                if self.model:
                    results = self.model(frame_rgb_lh, verbose=False)[0]
                    for box in results.boxes:
                        #x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cls = int(box.cls[0])
                        label = self.model.names[cls]
                        conf = box.conf[0].item()
                        cv2.rectangle(frame_rgb_lh, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame_rgb_lh, f"{label} {conf:.2f}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

                image_lh = QImage(frame_rgb_lh.data, frame_rgb_lh.shape[1], frame_rgb_lh.shape[0], QImage.Format_RGB888)
                pixmap_lh = self.crop_and_scale(image_lh, self.video_label_LH.width(), self.video_label_LH.height())
                self.video_label_LH.setPixmap(pixmap_lh)

    def crop_and_scale(self, image: QImage, target_width: int, target_height: int) -> QPixmap:
        img_ratio = image.width() / image.height()
        target_ratio = target_width / target_height

        if img_ratio > target_ratio:
            new_width = int(image.height() * target_ratio)
            x_offset = (image.width() - new_width) // 2
            cropped = image.copy(x_offset, 0, new_width, image.height())
        else:
            new_height = int(image.width() / target_ratio)
            y_offset = (image.height() - new_height) // 2
            cropped = image.copy(0, y_offset, image.width(), new_height)

        return QPixmap.fromImage(cropped).scaled(
            target_width, target_height,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )

    def start_detection(self):
        print("Starting detection... (placeholder for YOLO inference)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Century Gothic", 10)
    font.setBold(True)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
