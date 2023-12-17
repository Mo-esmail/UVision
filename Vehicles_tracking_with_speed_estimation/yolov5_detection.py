import torch
import math
import time
import sys
import cv2
sys.path.insert(0, './yolov5')

import torch.backends.cudnn as cudnn

from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import (non_max_suppression, scale_coords)
from yolov5.utils.torch_utils import select_device
from yolov5.utils.plots import Annotator, colors

from yolov5.utils.datasets import LoadImages, LoadStreams
from yolov5.utils.general import  check_img_size



class detector():
    def __init__(self, pth_yolo_model, model_attr, classes):

        # Model attributes
        (self.frame_size, self.conf_thres, self.iou_thres, self.device, self.max_detections, self.half, self.livecam) = model_attr
        self.classes = classes

        # initialize detection model
        self.device = select_device(self.device)
        self.model = DetectMultiBackend(pth_yolo_model, device=self.device)
        self.stride, self.names, self.pt, self.jit = self.model.stride, self.model.names, self.model.pt, self.model.jit


        # half precision only supported by PyTorch on CUDA
        self.half &= self.pt and self.device.type != 'cpu'
        if self.pt:
            self.model.model.half() if self.half else self.model.model.float()

        if self.pt and self.device.type != 'cpu':
            self.model(torch.zeros(1, 3, *self.frame_size).to(self.device).type_as(next(self.model.model.parameters())))

            # Get names and colors for different classes
        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names

    def detect(self, dataset, thread):

        self.window = thread.window
        self.thread = thread
        self.source = self.window.src
        self.new_video = True
        self.save_vid = thread.window.save_vid

        start = time.time()

        for num_frames, (_, frame, frames_src, vid_cap, _) in enumerate(dataset):
            if self.new_video:
                if vid_cap:  # video
                    fps = vid_cap.get(cv2.CAP_PROP_FPS)
                    w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                else:  # stream
                    fps, h, w = 11, len(frames_src[0]), len(frames_src[0][0])

                self.vid_writer = cv2.VideoWriter("output/out.avi", cv2.VideoWriter_fourcc(*'XVID'), fps, (w, h))
                self.new_video = False

            # Preprocess the input
            frame = self.preprocess_input(frame)

            # Inference using yolov5
            detections = self.model(frame, augment=False)

            # Apply NMS
            detections = non_max_suppression(detections, self.conf_thres, self.iou_thres, self.classes,
                                             max_det=self.max_detections)

            # postprocess the output

            self.postprocess_out(frames_src, frame, detections)

            # calc. FPS
            if num_frames % 10 == 0 and num_frames != 0:

                time_elapsed = time.time() - start

                fps = math.ceil(10 / time_elapsed)

                start = time.time()

                self.thread.update_fps.emit(str(fps))

    def preprocess_input(self, frame):

        # Preprocess the input
        frame = torch.from_numpy(frame).to(self.device)
        frame = frame.half() if self.half else frame.float()  # uint8 to fp16/32
        frame /= 255.0  # 0 - 255 to 0.0 - 1.0
        if frame.ndimension() == 3:
            frame = frame.unsqueeze(0)
        return frame

    def postprocess_out(self, frames_src, frame, detections):

        for i, det in enumerate(detections):

            if self.livecam:  # Livecam >> batch_size >= 1
                frame_src = frames_src[i].copy()
            else:
                frame_src = frames_src.copy()


            if det is not None and len(det):
                # Rescale boxes to source image size
                det[:, :4] = scale_coords(frame.shape[2:], det[:, :4], frame_src.shape).round()

                self.annotate(frame_src, det)

                if self.save_vid:
                    self.vid_writer.write(frame_src)

                # send frame to GUI
                self.thread.update_stream.emit(frame_src)



    def annotate(self, frame_src, outputs):
        annotator = Annotator(frame_src, line_width=2, pil=not ascii)

        # draw boxes for visualization
        if len(outputs) > 0:

            for output in outputs:

                bboxes = output[0:4]
                conf = output[4]
                cls = output[5]
                c = int(cls)  # integer class

                label = f'{self.names[c]} {conf: .2f}'
                annotator.box_label(bboxes, label, color=colors(c, True))

        return annotator


def yolov5_detect(thread):
    # files paths
    pth_yolo_model = "yolov5s.pt"
    window = thread.window
    pth_source = window.src


    # classes to bet tracked
    classes = None
    # model attributes
    device = thread.window.device
    webcam= pth_source=='0' or pth_source.startswith( 'rtsp') or pth_source.startswith('http') or pth_source.endswith('.txt')
    conf_thres = thread.window.conf_thres
    iou_thres = thread.window.iou_thres
    max_detections = 100  # maximum detections per image
    half = True
    frame_size = [320]
    frame_size *= 2 if len(frame_size) == 1 else 1

    # aggregate attributes to send to tracker class
    model_attr = (frame_size, conf_thres, iou_thres, device, max_detections, half,webcam)

    model = detector(pth_yolo_model, model_attr, classes)

    # check new size ration
    frame_size = check_img_size(frame_size, s=model.stride)

    # Dataloader
    if webcam:
        cudnn.benchmark = True  # set True to speed up constant image size inference
        dataset = LoadStreams(pth_source, img_size=frame_size, stride=model.stride, auto=model.pt and not model.jit)
    else:
        dataset = LoadImages(pth_source, img_size=frame_size, stride=model.stride, auto=model.pt and not model.jit)


    model.detect(dataset, thread)