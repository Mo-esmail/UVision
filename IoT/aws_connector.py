import boto3
import json
from botocore.exceptions import NoCredentialsError
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder


class AWSConnector():

    def __init__(self,cred):

        self.creds = cred
        # MQTT Connection Objects
        self.event_loop_group = io.EventLoopGroup(1)
        self.host_resolver = io.DefaultHostResolver(self.event_loop_group)
        self.client_bootstrap = io.ClientBootstrap(self.event_loop_group, self.host_resolver)
        self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=self.creds.ENDPOINT,
            cert_filepath=self.creds.PATH_TO_CERT,
            pri_key_filepath=self.creds.PATH_TO_KEY,
            client_bootstrap=self.client_bootstrap,
            ca_filepath=self.creds.PATH_TO_ROOT,
            client_id=self.creds.CLIENT_ID,
            clean_session=False,
            keep_alive_secs=30
        )        
        print(f"Conntecting to {self.creds.ENDPOINT} with client ID {self.creds.CLIENT_ID}")
        # Make the connect() call
        connect_future = self.mqtt_connection.connect()
        # Future.result() waits until a result is available
        connect_future.result()
        print("Connected!")
        

    def send_message(self,num_vehicles):
        print("Publishing begins")
        message = {"DeviceID": self.creds.DeviceId, "location": self.creds.Location,"num_vehicles": num_vehicles}
        self.mqtt_connection.publish(topic=self.creds.Topic, payload=json.dumps(message), qos=mqtt.QoS.AT_LEAST_ONCE)
       # print("Published: '" + json.dumps(message) + "' to the topic: " + Credentials.Topic)
        print(f"Message {json.dumps(message)} has been published to the topic {self.creds.Topic}")
        # print('Publish End')

    def disconnect(self):
        print("Disconnecting ...")
        disconnect_future = self.mqtt_connection.disconnect()
        disconnect_future.result()
        print("Disconnected")
    
    def upload_to_s3(self):
        s3 = boto3.client('s3', aws_access_key_id=self.creds.ACCESS_KEY,
                          aws_secret_access_key=self.creds.SECRET_KEY)
        try:
            s3.upload_file(self.creds.LocalPic, self.creds.BucketName, self.creds.file_key)
            print("Upload Successful")
            # print("Upload Successful")
            return True
        except FileNotFoundError:
            print("The file was not found")
            # print("The file was not found")
            return False
        except NoCredentialsError:
            print("Credentials not available")
            # print("Credentials not available")
            return False