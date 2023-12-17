import cv2
import glob
import numpy as np
from VIF import ViF

# get feature vector for dataset
data = []
for file in glob.glob("dataset/no_accidents/*.avi"):
    print(file)
    cap = cv2.VideoCapture(file)
    frames = []
    max_num_frames = 60
    count = 1
    vif = ViF()

    while True:
        ret, frame = cap.read()

        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frames.append(gray)

        else:
            break

    obj = ViF()
    feature_vec = obj.process(frames)
    data.append(feature_vec)

np.savetxt("models/data_no_accident.csv", data, delimiter=",")
