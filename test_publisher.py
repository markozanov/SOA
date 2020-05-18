import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))


client = mqtt.Client()
client.on_connect = on_connect

payload = f"""
        {{
            "user_id": "51321",
            "server_id": "32168"
}}
"""

command = f"""
        {{
        "command_id": 10,
        "final": "true",
        "line_or_output": "Success",
        "result_code": 200,
        "killed": false
}}
"""

client.connect("localhost", 1883, 60)
client.publish("/login", payload)
# client.publish("/command_output/54654/5646525", command)
