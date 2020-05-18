import paho.mqtt.client as mqtt
import requests
import db_connection
import json


# def activate_server(user_id, server_id):


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))


def feedback(user_id, server_id):
    myobj = {'user_id': user_id, 'server_id': server_id}
    response = requests.post(f"http://localhost:8000/licenses/{user_id}", data=myobj).json()
    user_has_payed = True
    valid_to = None
    if "detail" in response:
        user_has_payed = False
    else:
        valid_to = response["valid_to"]

    # Fill DB even if valid_to is None
    db_connection.input_server(server_id, valid_to)

    print(response)
    print(server_id)
    print(user_id)
    print(valid_to)
    client = mqtt.Client()
    client.on_connect = on_connect

    client.connect("localhost", 1883, 60)

    if user_has_payed:
        client.publish(f"/login/{user_id}/{server_id}", "Success")
        # activate_server(user_id, server_id)
    else:
        client.publish(f"/login/{user_id}/{server_id}", "Failure")


# feedback("654asd", "sad72")

