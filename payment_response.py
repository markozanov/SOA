import paho.mqtt.client as mqtt
import requests
import json


# def activate_server(user_id, server_id):


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))


def feedback(user_id, server_id):
    response = requests.get(f"http://localhost:8000/licenses/{user_id}").json()
    user_has_payed = response["Response"]
    print(response)
    print(server_id)
    print(user_id)
    client = mqtt.Client()
    client.on_connect = on_connect

    client.connect("localhost", 1883, 60)

    if user_has_payed:
        client.publish(f"/login/{user_id}/{server_id}", "Success")
        # activate_server(user_id, server_id)
    else:
        client.publish(f"/login/{user_id}/{server_id}", "Failure")


# feedback("654asd", "sad72")

