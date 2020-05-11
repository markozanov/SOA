import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))


def run(command, user):
    client = mqtt.Client()
    client.on_connect = on_connect

    # command_id = AUTO_GENERATE
    command_type = command.command_type
    body = command.body
    servers = command.target_servers
    payload = f"""{{
                "command_id": 10,
                "command_type": "{command_type}",
                "body": "{body}"
            }}"""

    client.connect("localhost", 1883, 60)
    for server in servers:
        client.publish(f"/commands/{user}/{server}", payload)
