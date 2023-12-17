import sys

sys.path.insert(0, "./yolov5")
from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import scale_coords, non_max_suppression, check_img_size
from yolov5.utils.augmentations import letterbox

import glob
import cv2
import dlib
import random
from VIF import ViF
import pickle
import torch
from time import time

clf = pickle.load(open("models\model-svm-ang.sav", "rb"))
total_frames = []
sub_sampling = 29
counter_sub_video = 1
data = []


class Tracker:
    def __init__(self, frame, rec, name, frame_index):
        xmin = rec[0]
        ymin = rec[1]
        xmax = rec[2]
        ymax = rec[3]
        self.tracker = dlib.correlation_tracker()
        self.tracker.start_track(frame, dlib.rectangle(xmin, ymin, xmax, ymax))
        self.name = name
        self.frame_index = frame_index
        self.history = [dlib.rectangle(xmin, ymin, xmax, ymax)]
        self.flow_vectors = []

    def update(self, frame):
        self.tracker.update(frame)
        return self.tracker.get_position()

    def get_position(self):
        return self.tracker.get_position()

    def add_history(self, pos):
        self.history.append(pos)

    def get_box_from_history(self, frame_width, frame_height):

        xmin = self.history[0].left()
        ymin = self.history[0].top()
        xmax = self.history[0].right()
        ymax = self.history[0].bottom()
        for pos in self.history:
            if pos.left() < xmin:
                xmin = pos.left()
            if pos.right() > xmax:
                xmax = pos.right()
            if pos.top() < ymin:
                ymin = pos.top()
            if pos.bottom() > ymax:
                ymax = pos.bottom()

        if xmin < 0:
            xmin = 0
        if ymin < 0:
            ymin = 0
        if xmax > frame_width:
            xmax = frame_width - 1
        if ymax > frame_height:
            ymax = frame_height - 1

        return (int(xmin), int(ymin), int(xmax), int(ymax))

    def add_vector(self, line):
        self.flow_vectors.append(line)

    def clean_flow_vector(self):
        self.flow_vectors = []

    def is_inside(self, line):
        pos = self.get_position()
        if (
            line[0] > pos.left()
            and line[1] > pos.top()
            and line[0] < pos.right()
            and line[1] < pos.bottom()
        ):
            return True
        elif (
            line[2] > pos.left()
            and line[3] > pos.top()
            and line[2] < pos.right()
            and line[3] < pos.bottom()
        ):
            return True
        else:
            return False


# process vif for each tracker
def vif(trackers, frame_width, frame_height, frame):
    crashes_detected = []
    global sub_sampling
    print("input each tracker to the vif descriptor")
    global counter_sub_video
    if len(trackers) == 0:
        print("No trakers found!!")
    for i, tracker in enumerate(trackers):
        print(
            "process with vif tracker " + str(tracker.name),
            tracker.get_position().right() - tracker.get_position().left(),
            tracker.get_position().bottom() - tracker.get_position().top(),
        )

        box = tracker.get_box_from_history(frame_width, frame_height)

        if box[2] - box[0] < 100:
            print("the trackers dims is very small it will be ignored")
            continue

        print(
            "tracker frame_index:",
            tracker.frame_index,
            "len history:",
            len(tracker.history),
        )
        if len(tracker.history) < sub_sampling:
            print("tracker have a few frames it will be ignored")
        else:

            counter_sub_video += 1

            tracker_frames = []

            for j in range(
                tracker.frame_index, tracker.frame_index + len(tracker.history)
            ):

                img = total_frames[j]
                sub_image = img[box[1] : box[3], box[0] : box[2]]
                gray_image = cv2.cvtColor(sub_image, cv2.COLOR_BGR2GRAY)
                tracker_frames.append(gray_image)

            print("tracker with " + str(len(tracker_frames)) + " frames")
            # procesing vif
            obj = ViF()
            feature_vec = obj.process(tracker_frames)
            data.append(feature_vec)

            feature_vec = feature_vec.reshape(1, 304)
            result = clf.predict(feature_vec)
            print("RESULT SVM", result[0])

            if result[0] == 1:
                crashes_detected.append([box[0], box[1], box[2], box[3]])

    return crashes_detected


def preprocess_input(frame):

    # Preprocess the input
    frame = torch.from_numpy(frame).to("cpu")
    frame = frame.float()  # uint8 to fp16/32
    frame /= 255.0  # 0 - 255 to 0.0 - 1.0
    if frame.ndimension() == 3:
        frame = frame.unsqueeze(0)
    frame = frame.permute(0, 3, 1, 2)
    return frame


def start_process(path):
    global total_frames
    print("reading video " + path)
    total_frames = []

    pth_yolo_model = "yolov5m.pt"
    model = DetectMultiBackend(pth_yolo_model, device=torch.device("cpu"))
    names = model.module.names if hasattr(model, "module") else model.names

    conf_thres = 0.5
    iou_thres = 0.5
    max_detections = 100

    cap = cv2.VideoCapture(path)

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    print(" frames in video: " + str(frame_count) + "frame rate: " + str(fps))

    index = 0

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    frame_size = frame_width
    frame_size = check_img_size(frame_size)

    trackers = []

    crashes_detected = []
    out = cv2.VideoWriter(
        "outpy.avi",
        cv2.VideoWriter_fourcc("M", "J", "P", "G"),
        25,
        (frame_width, frame_height),
    )

    while True:
        ret, frame = cap.read()

        if ret:
            new_frame = frame.copy()

            total_frames.append(new_frame)

            # save time to calc. FPS
            start = time()

            # resize frames with proper aspect ratio
            frame = letterbox(frame, frame_size, model.stride)[0]

            # las veces que se eejcua ViF
            if index > 0 and (
                index % sub_sampling == 0 or index == frame_count - 1
            ):  # remove vid config
                print("FRAME " + str(index) + " VIF")
                crashes_detected = vif(trackers, frame_width, frame_height, frame)
                print("Crashes NO. ", len(crashes_detected))
                if len(crashes_detected) > 0:
                    cv2.putText(
                        frame,
                        "Crash",
                        (10, 40),
                        cv2.FONT_HERSHEY_COMPLEX_SMALL,
                        1,
                        (0, 0, 200),
                        2,
                        cv2.LINE_AA,
                    )
                    cv2.imshow("Accident preview", frame)
                    cv2.waitKey(1)

            # new detections with yolo
            if index % sub_sampling == 0 or index == 0:
                print("FRAME " + str(index) + " YOLO")
                trackers = []

                frame = preprocess_input(frame)

                detections = model.forward(frame)

                detections = non_max_suppression(
                    detections, conf_thres, iou_thres, max_det=max_detections
                )

                for i, detecs in enumerate(detections):
                    if detecs is not None and len(detecs):
                        detecs[:, :4] = scale_coords(
                            frame.shape[2:], detecs[:, :4], new_frame.shape
                        ).round()
                        # annotator = Annotator(new_frame, line_width=2, pil=not ascii)
                        for det in detecs:

                            box = det[0:4]
                            accuracy = det[4]
                            label = det[5]
                            label = int(label)

                            xmin, ymin = int(box[0]), int(box[1])
                            xmax, ymax = int(box[2]), int(box[3])

                            print("yolo detection: ", names[label])

                            if names[label] in ["car", "truck"]:
                                print("car finded")

                                cv2.rectangle(
                                    new_frame, (xmin, ymin), (xmax, ymax), (0, 0, 255)
                                )

                                if xmax < frame_width and ymax < frame_height:
                                    tracker_rect = (xmin, ymin, xmax, ymax)
                                    tr = Tracker(
                                        new_frame,
                                        tracker_rect,
                                        random.randrange(100),
                                        index,
                                    )
                                    trackers.append(tr)
                                else:
                                    if xmax < frame_width and ymax >= frame_height:
                                        tracker_rect = (
                                            xmin,
                                            ymin,
                                            xmax,
                                            frame_height - 1,
                                        )
                                        tr = Tracker(
                                            new_frame,
                                            tracker_rect,
                                            random.randrange(100),
                                            index,
                                        )
                                    elif xmax >= frame_width and ymax < frame_height:
                                        tracker_rect = (
                                            xmin,
                                            ymin,
                                            frame_width - 1,
                                            ymax,
                                        )
                                        tr = Tracker(
                                            new_frame,
                                            tracker_rect,
                                            random.randrange(100),
                                            index,
                                        )
                                    else:
                                        tracker_rect = (
                                            xmin,
                                            ymin,
                                            frame_width - 1,
                                            frame_height - 1,
                                        )
                                        tr = Tracker(
                                            new_frame,
                                            tracker_rect,
                                            random.randrange(100),
                                            index,
                                        )
                                    trackers.append(tr)

            else:
                print("FRAME " + str(index) + " UPDATE TRACKER")

                # update trackers
                for i, tracker in enumerate(trackers):
                    tr_pos = tracker.update(new_frame)
                    if (
                        tr_pos.left() > 0
                        and tr_pos.top() > 0
                        and tr_pos.right() < frame_width
                        and tr_pos.bottom() < frame_height
                    ):
                        cv2.rectangle(
                            new_frame,
                            (int(tr_pos.left()), int(tr_pos.top())),
                            (int(tr_pos.right()), int(tr_pos.bottom())),
                            (0, 255, 0),
                        )
                        tracker.add_history(tr_pos)

            out.write(new_frame)

            end = time()
            fps = 1 / (end - start)

            print(f"FPS: {fps:.2f}")
            cv2.imshow("processing preview", new_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            index += 1

        else:
            break

    cv2.destroyAllWindows()


# start_process("test_data/1519.mp4")

for file in glob.glob("dataset_test/accidents/*.mp4"):
    start_process(file)
