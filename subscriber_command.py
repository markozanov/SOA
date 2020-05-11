import paho.mqtt.client as mqtt
import json


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))


def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    print(payload)
    nothing, topic, user_id, server_id = msg.topic.split("/")
    print("Topic: " + topic + "\nUser ID: " + user_id + "\nServer Id: " + server_id)
    # return_to_user(payload["line_or_output"])


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

client.subscribe("/command_output/#")

client.loop_forever()

# def return_to_user(output):
