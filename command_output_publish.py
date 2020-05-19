import paho.mqtt.client as mqtt

client = mqtt.Client()

# payload = f"""
#         {{
#             "user_id": "51321",
#             "server_id": "32168"
# }}
# """

command = f'''
        {{
        "command_id": 10,
        "final": true,
        "line_or_output": "Success",
        "result_code": 200,
        "killed": false
}}
'''

client.username_pw_set('user_01', 'passwd01')
client.connect('localhost', 1883, 60)
client.publish('/command_output/viktor/def', command)
print('done')
