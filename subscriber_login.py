import paho.mqtt.client as mqtt
import json
import payment_response as resp


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))


def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode("UTF-8"))
    print(payload["user_id"])
    print(payload["server_id"])
    user_id = payload["user_id"]
    server_id = payload["server_id"]
    resp.feedback(user_id, server_id)

    # request_to_payment(user_id, server_id)
    # register_server(user_id, server_id)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

client.subscribe("/login")

client.loop_forever()

# def register_server(user_id, server_id):
#     MORE MAGIC
