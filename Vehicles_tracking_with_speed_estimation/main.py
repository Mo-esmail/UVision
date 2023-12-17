import sys
import cv2
import numpy as np
import re
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi

import yolov5_detection
import yolov5_tracking

from aws_connector.aws_connector import AWSConnector
from aws_connector.Credentials import Credentials

class workerModel(QThread):
    update_stream = pyqtSignal(np.ndarray)
    update_fps = pyqtSignal(str)
    update_num_vehicles = pyqtSignal(str)
    update_avg_speed = pyqtSignal(str)

    def __init__(self, window, model, parent=None):
        QThread.__init__(self, parent)
        self.model = model
        self.window = window
        self.isRunning = True

    def run(self):

        while self.isRunning:
            self.model(self)


    def stop(self):
        self.isRunning = False
        self.terminate()
        self.wait()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        loadUi('UI/main.ui', self)

        self.UI_component_init()
        self.connect_buttons()
        self.connect_chkboxes_radio()

        ## default values
        self.flag_snd2aws = False
        self.save_vid = False
        self.src = '0'
        self.conf_thres = 0.4
        self.iou_thres= 0.5
        self.device= 'cpu'

    def UI_component_init(self):
        self.setFixedSize(1152, 638)
        self.setWindowIcon(QIcon("UI/icon.png"))
        self.setWindowTitle("Smart traffic analysis")
        self.bttn_start_processing.setEnabled(False)
        self.bttn_stop_model.setEnabled(False)
        self.tb_console.clear()
        self.lbl_fps.clear()
        self.lbl_vehicles.clear()
        self.lbl_avg_speed.clear()
        self.connect_aws()

        # hide result labels
        # hide tracking headers
        self.lbl_vehicles.hide()
        self.lbl_vehicles_head.hide()
        self.lbl_avg_speed.hide()
        self.lbl_avg_speed_head.hide()
        self.lbl_speed_unit.hide()
        self.lbl_traffic_head.hide()
        self.lbl_traffic.hide()

    def connect_buttons(self):
        self.bttn_start_processing.clicked.connect(self.call_model)
        self.bttn_select_source.clicked.connect(self.select_src)
        self.bttn_stop_model.clicked.connect(self.stop_model)

    def connect_chkboxes_radio(self):
        self.chkbox_snd2aws.stateChanged.connect(self.send_data_aws)
        self.chk_save_out.stateChanged.connect(self.save_output)
        self.livecam_radio.clicked.connect(self.set_livecam)
        self.video_radio.clicked.connect(self.set_video)

    def save_output(self):
        if self.chk_save_out.checkState():
            self.save_vid = True
        else:
            self.save_vid = False

    def connect_aws(self):
        # Initialize Aws
        cred = Credentials()
        self.aws_connector = AWSConnector(cred, self)
        self.lbl_aws_connect.setText("Connected to AWS")
        self.lbl_aws_connect.setStyleSheet("color: green")
        self.flag_aws = True

    def call_model(self):

        self.device = self.device_box.currentText()
        self.conf_thres = float(self.te_conf.toPlainText())
        self.iou_thres = float(self.te_iou.toPlainText())

        #disable model attributes
        self.te_conf.setEnabled(False)
        self.te_iou.setEnabled(False)
        self.device_box.setEnabled(False)

        model = None
        if self.model_box.currentText() == "Yolov5_speed estimation":
            self.lbl_vehicles.show()
            self.lbl_vehicles_head.show()
            self.lbl_avg_speed.show()
            self.lbl_avg_speed_head.show()
            self.lbl_speed_unit.show()

            model = yolov5_tracking.yolov5_mot

        elif self.model_box.currentText() == "Yolov5_detection" :


            model = yolov5_detection.yolov5_detect
        else:
            self.tb_console.append("The model is not found")

        if model is not None:
            self.bttn_stop_model.setEnabled(True)
            self.bttn_start_processing.setEnabled(False)
            self.model_thread = workerModel(window=self, model=model)
            self.model_thread.start()
            self.model_thread.update_fps.connect(self.lbl_fps.setText)
            self.model_thread.update_stream.connect(self.display_frame)
            self.model_thread.update_num_vehicles.connect(self.lbl_vehicles.setText)
            self.model_thread.update_avg_speed.connect(self.lbl_avg_speed.setText)

    def set_livecam(self):
        self.lbl_source_status.setText("Insert the cam address")

    def set_video(self):
        self.lbl_source_status.setText("Select video")

    def select_src(self):
        if self.video_radio.isChecked():
            self.src = QFileDialog.getOpenFileName(self, caption='Select a video')[0]
            self.te_livecam.setPlainText( self.src)
            self.lbl_source_status.setText("Video loaded")
            self.lbl_source_status.setStyleSheet("color: green")
            self.bttn_start_processing.setEnabled(True)

        elif self.livecam_radio.isChecked():
            src = self.te_livecam.toPlainText()
            if src =='0' or src.startswith( 'rtsp') or src.startswith('http') or src.endswith('.txt'):
                self.src = src
                self.lbl_source_status.setText("Livecam loaded ")
                self.lbl_source_status.setStyleSheet("color: green")
                self.bttn_start_processing.setEnabled(True)
            else:
                self.lbl_source_status.setText("Invalid Livecam")
                self.lbl_source_status.setStyleSheet("color: red")


    def stop_model(self):
        self.model_thread.stop()
        self.lbl_fps.clear()
        self.stream_space.clear()
        self.bttn_start_processing.setEnabled(True)
        self.bttn_stop_model.setEnabled(False)

    def send_data_aws(self):
        if self.flag_aws and self.chkbox_snd2aws.checkState():
            self.flag_snd2aws = True
        else:
            self.flag_snd2aws = False

    def display_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, c = frame.shape
        if frame.shape[0]>430:
            h = 430
        if frame.shape[1]>920:
            w = 920
        
        frame = cv2.resize(frame, (w, h))

        step = c*w

        frame_vis = QImage(frame.data, w, h, step, QImage.Format_RGB888)


        self.stream_space.setPixmap(QPixmap.fromImage(frame_vis))



def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
