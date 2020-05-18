from fastapi import FastAPI
from pydantic import BaseModel
import command_publisher
import random

app = FastAPI()


class Users(BaseModel):
    user_list: list


class Command(BaseModel):
    target_servers: list
    command_type: str
    body: str


class UserInfo(BaseModel):
    command: Command
    user_id: str


class Groups(BaseModel):
    group_list: list


@app.get("/service_instance_management")
def read_root():
    return {"Hello": "World"}


@app.put("/share/{server_id}")
def share_server(server_id: int, users: Users):
    execute_sharing(server_id, users.user_list)
    return f"Share server {server_id} with user(s) {users.user_list}"


@app.put("/group/{server_id}")
def group_server(server_id: int, groups: Groups):
    execute_grouping(server_id, groups.group_list)
    return f"Share server {server_id} with user(s) {groups.group_list}"


@app.put("/run")
def execute_command(user_info: UserInfo):
    user_id = user_info.user_id
    command = user_info.command
    print(user_id)
    print(command.target_servers)
    print(command.body)
    print(command.command_type)

    # CHECK PERMISSION
    command_publisher.run(command, user_id)
    return "Success"


# SIMULATION - TEST ONLY
@app.get("/licenses/{user_id}")
def confirm_license(user_id: str):
    number = random.randrange(10)
    success = False
    if number > 5:
        success = True
    return {"User": user_id,
            "Response": success}


def execute_sharing(server_id, users):
    # UPDATE DATABASE
    print(server_id)
    print(users)


def execute_grouping(server_id, groups):
    # UPDATE DATABASE
    print(server_id)
    print(groups)
