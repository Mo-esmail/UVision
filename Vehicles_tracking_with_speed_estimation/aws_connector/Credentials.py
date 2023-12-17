import os
from dotenv import load_dotenv

class Credentials:
    # Define ENDPOINT, CLIENT_ID, PATH_TO_CERT, PATH_TO_KEY, PATH_TO_ROOT, MESSAGE, TOPIC, and RANGE
    # from start import DeviceId
    def __init__(self) -> None:
        load_dotenv()
        self.ENDPOINT = os.environ['ENDPOINT']
        self.CLIENT_ID = os.environ['CLIENT_ID']
        self.PATH_TO_CERT = os.environ['PATH_TO_CERT']
        self.PATH_TO_KEY = os.environ['PATH_TO_KEY']
        self.PATH_TO_ROOT = os.environ['PATH_TO_ROOT']
        self.ACCESS_KEY = os.environ['ACCESS_KEY']
        self.SECRET_KEY = os.environ['SECRET_KEY']
        self.DeviceId = os.environ['DeviceId']
        self.Location = os.environ['Location']
        self.LocalPic = os.environ['LocalPic']
        self.BucketName = os.environ['BucketName']
        self.Topic = f"iot/{self.DeviceId}"
        self.file_key = f"Accidant{self.DeviceId}.jpg"
