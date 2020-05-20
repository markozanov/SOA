import asyncio
import json
import socket
import time
from datetime import datetime

import asyncpg
import paho.mqtt.client as mqtt
import requests
import uvicorn
from asyncpg.pool import Pool
from consul import Check, Consul
from fastapi import FastAPI, Response, status
from pydantic import BaseModel


class ShareServer(BaseModel):
    user_id: str
    target_user: str
    server_id: str


class GroupServer(BaseModel):
    group_id: int
    server_id: str


class CreateGroup(BaseModel):
    name: str
    created_by: str


class RunCommand(BaseModel):
    body: str
    user_id: str
    target_servers: list


class StopCommand(BaseModel):
    command_id: int


time.sleep(30)

consul = Consul(host='consul', port=8500)
agent = consul.agent

postgres_connection_string = 'postgresql://postgres:instancemanager@postgres:5432/postgres'
pool = None

loop = asyncio.get_event_loop()
command_output_connection = loop.run_until_complete(
    asyncpg.connect(postgres_connection_string))

login_connection = loop.run_until_complete(
    asyncpg.connect(postgres_connection_string))
login_publish_client = mqtt.Client()
login_publish_client.username_pw_set('user_01', 'passwd1')
login_publish_client.connect('emqx')

command_publish_client = mqtt.Client()
command_publish_client.username_pw_set('user_01', 'passwd01')
command_publish_client.connect('emqx')

app = FastAPI()


def get_payment_service_url():
    service_list = agent.services()
    service_info = service_list['payment']
    host = service_info['Address']
    port = service_info['Port']
    return f'http://{host}:{port}/licences/server'


def command_output_on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    print(f'command output message payload: {payload}')
    _, topic, user_id, server_id = msg.topic.split("/")
    stopped = payload['final'] or payload['killed']
    if stopped:
        print('stopping command')
        loop.run_until_complete(command_output_connection.execute(
            'update command set running = False where id = $1', payload['command_id']))


def login_subscriber_on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode('UTF-8'))
    print(f'login message payload: {payload}')
    user_id = payload['user_id']
    server_id = payload['server_id']
    epoch = str(datetime.fromtimestamp(0))
    print(f'inserting server instance {server_id}')
    loop.run_until_complete(login_connection.execute(
        'insert into server_instance (server_id, active) values ($1, $2)', server_id, epoch))
    print(f'inserting user server ({user_id}, {server_id})')
    loop.run_until_complete(login_connection.execute(
        'insert into user_server (user_id, server_id) values ($1, $2)', user_id, server_id))
    url = get_payment_service_url()
    payload = {'user_id': user_id, 'server_id': server_id}
    print(f'contacting payment at {url} with payload {payload}')
    response = requests.post(url, data=payload).json()
    print(f'{response}')
    if 'detail' in response:
        print(f'publishing login failure for user: {user_id}, server: {server_id}')
        login_publish_client.publish(
            f'/login/{user_id}/{server_id}', 'Failure')
    else:
        valid_to = response['valid_to']
        print(f'updating server active until {valid_to}')
        loop.run_until_complete(login_connection.execute(
            'update server_instance set active = $1 where id = $2', valid_to, server_id))
        print(f'publishing login success for user: {user_id}, server: {server_id}')
        login_publish_client.publish(
            f'/login/{user_id}/{server_id}', 'Success')


def row_to_command(row):
    return {'id': row['id'], 'body': row['body'], 'type': row['type'], 'user_id': row['user_id'], 'server_id': row['server_id']}


async def check_server(server_id, conn):
    row = await conn.fetchrow('select id, active from server_instance where id = $1', server_id)
    if row is None:
        return 'unknown'
    active = datetime.fromisoformat(str(row['active']))
    if active <= datetime.now():
        return 'expired'
    return 'ok'


async def check_user_server(user_id, server_id, conn):
    return await conn.fetchrow(
        'select user_id, server_id from user_server where user_id = $1 and server_id = $2',
        user_id, server_id)


@app.on_event('startup')
async def create_pool():
    global pool
    pool = await asyncpg.create_pool(
        user='postgres',
        password='instancemanager',
        database='postgres',
        host='postgres',
        port=5432,
        min_size=0,
        max_size=4
    )


@app.on_event('shutdown')
async def close_pool():
    await pool.close()


@app.get('/')
async def root():
    return 'instancemanager'


@app.get('/command/list')
async def command_list():
    async with pool.acquire() as conn:
        commands = await conn.fetch('select id, body, type, user_id, server_id from command where running = True')
        return list(map(row_to_command, commands))


@app.post('/server/share', status_code=200)
async def server_share(ss: ShareServer, res: Response):
    async with pool.acquire() as conn:
        cs = await check_server(ss.server_id, conn)
        if cs == 'unknown':
            res.status_code = status.HTTP_400_BAD_REQUEST
            return {'error': f'Unknown server id: {ss.server_id}'}
        elif cs == 'expired':
            res.status_code = status.HTTP_403_FORBIDDEN
            return {'error': f'The server licence for server {ss.server_id} has expired'}
        if await check_user_server(ss.user_id, ss.server_id, conn) is None:
            res.status_code = status.HTTP_403_FORBIDDEN
            return {'error': f'You do not have permission to share this server'}
        await conn.execute('insert into user_server (user_id, server_id) values ($1, $2)', ss.target_user, ss.server_id)
        return Response()


@app.post('/group/create')
async def create_group(cg: CreateGroup):
    async with pool.acquire() as conn:
        await conn.execute('insert into group_instance (name, created_by) values ($1, $2)', cg.name, cg.created_by)
        return Response()


@app.post('/server/group', status_code=200)
async def group(gs: GroupServer, res: Response):
    async with pool.acquire() as conn:
        group = await conn.fetchrow('select id from group_instance where id = $1', gs.group_id)
        if group is None:
            res.status_code = status.HTTP_400_BAD_REQUEST
            return {'error': f'Unknown group id: {gs.group_id}'}
        cs = await check_server(gs.server_id, conn)
        if cs == 'unknown':
            res.status_code = status.HTTP_400_BAD_REQUEST
            return {'error': f'Unknown server id: {gs.server_id}'}
        elif cs == 'expired':
            res.status_code = status.HTTP_403_FORBIDDEN
            return {'error': f'The server licence for server {gs.server_id} has expired'}
        await conn.execute('insert into group_server (group_id, server_id) values ($1, $2)', gs.group_id, gs.server_id)
        return Response()


@app.post('/command/run', status_code=200)
async def command_run(rc: RunCommand, res: Response):
    result = []
    async with pool.acquire() as conn:
        for server_id in rc.target_servers:
            cs = await check_server(server_id, conn)
            if cs == 'unknown':
                res.status_code = status.HTTP_400_BAD_REQUEST
                return {'error': f'Unknown server id: {server_id}'}
            elif cs == 'expired':
                res.status_code = status.HTTP_403_FORBIDDEN
                return {'error': f'The server licence for server {server_id} has expired'}
            if await check_user_server(rc.user_id, server_id, conn) is None:
                res.status_code = status.HTTP_403_FORBIDDEN
                return {'error': f'You do not have permission to run commands on the server: {server_id}'}
            id = await conn.fetchval(
                'insert into command (body, running, user_id, server_id) values ($1, True, $2, $3) returning id',
                rc.body, rc.user_id, server_id)
            result.append({'server_id': server_id, 'command_id': id})
            payload = f'''{{
                "command_id": {id},
                "command_type": "start",
                "body": "{rc.body}"
            }}'''
            command_publish_client.publish(
                f'/commands/{rc.user_id}/{server_id}', payload)
        return result


@app.post('/command/stop')
async def command_stop(sc: StopCommand):
    async with pool.acquire() as conn:
        command = await conn.fetchrow('select user_id, server_id from command where id = $1', sc.command_id)
        payload = f'''{{
            "command_id": {sc.command_id},
            "command_type": "stop",
            "body": ""
        }}'''
        user_id = command['user_id']
        server_id = command['server_id']
        command_publish_client.publish(
            f'/commands/{user_id}/{server_id}', payload)
        return Response()


if __name__ == '__main__':
    service = agent.service
    check = Check.http('http://instancemanager:5000/',
                       interval='10s', timeout='5s', deregister='1s')
    ip = socket.gethostbyname('instancemanager')
    service.register('instancemanager', service_id='instancemanager',
                     address=ip, port=5000, check=check)
    print('registered with consul')

    command_output_client = mqtt.Client()
    command_output_client.username_pw_set('user_01', 'passwd01')
    command_output_client.on_message = command_output_on_message
    command_output_client.connect('emqx')
    command_output_client.subscribe('/command_output/#')
    command_output_client.loop_start()
    print('subscribed to /command_output/#')

    login_subscriber_client = mqtt.Client()
    login_subscriber_client.username_pw_set('user_01', 'passwd01')
    login_subscriber_client.on_message = login_subscriber_on_message
    login_subscriber_client.connect('emqx')
    login_subscriber_client.subscribe('/login')
    login_subscriber_client.loop_start()
    print('subscribed to /login')

    print('starting server')
    uvicorn.run(app, host='0.0.0.0', port=5000, log_level='info')
