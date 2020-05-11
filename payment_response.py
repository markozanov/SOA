import paho.mqtt.client as mqtt

# GET USER_HAS_PAYED()
# user_has_payed = true/false


user_has_payed = False  #
user_id = 0  # TEMPORARY
server_id = 0  #


# def activate_server(user_id, server_id):


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))


client = mqtt.Client()
client.on_connect = on_connect

client.connect("localhost", 1883, 60)

if user_has_payed:
    client.publish(f"/login/{user_id}/{server_id}", "Success")
    # activate_server(user_id, server_id)
else:
    client.publish(f"/login/{user_id}/{server_id}", "Failure")
