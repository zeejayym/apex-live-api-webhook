import os
from dotenv import load_dotenv

import asyncio
import socket
import websockets
import logging

from events_pb2 import *
from aiohttp import web, ClientSession
import aiohttp_jinja2
import jinja2

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('websocket_server')

websockets_connected = set()
roleToken = os.getenv('roleToken')

def create_lobby():
    request = Request()
    request.customMatch_CreateLobby.CopyFrom(CustomMatch_CreateLobby())
    request.withAck = True  # Request an acknowledgement of your request by setting `withAck` to true

    for ws in websockets_connected:
        asyncio.create_task(ws.send(request.SerializeToString()))


def join_lobby():
    request = Request()
    request.customMatch_JoinLobby.CopyFrom(CustomMatch_JoinLobby(roleToken=roleToken))
    request.withAck = True  # Request an acknowledgement of your request by setting `withAck` to true

    for ws in websockets_connected:
        asyncio.create_task(ws.send(request.SerializeToString()))

# leave lobby possibly not working, getting success but not happening
def leave_lobby():
    request = Request()
    request.customMatch_LeaveLobby.CopyFrom(CustomMatch_LeaveLobby())
    request.withAck = True  # Request an acknowledgement of your request by setting `withAck` to true

    for ws in websockets_connected:
        asyncio.create_task(ws.send(request.SerializeToString()))


def send_chat(message):
    request = Request()
    request.customMatch_SendChat.CopyFrom(CustomMatch_SendChat(text=message))
    
    request.withAck = True

    for ws in websockets_connected:
        asyncio.create_task(ws.send(request.SerializeToString()))

def get_players():
    request = Request()
    request.customMatch_GetLobbyPlayers.CopyFrom(customMatch_GetLobbyPlayers())
    request.withAck = True

    for ws in websockets_connected:
        asyncio.create_task(ws.send(request.SerializeToString()))

async def send_chat_request(request):
    if request.method == 'POST':
        data = await request.post()  # Extract form data for POST requests
        message = data.get('Message')
        print(message)
        # Your logic to handle the message
        send_chat(message)
        return web.json_response({'status': 'Message sent'})
    else:
        # Handle GET request or return an error
        return web.json_response({'error': 'Method Not Allowed'}, status=405)

async def get_players_request(request):
    response = get_players()
    return web.json_response(response)


async def create_lobby_request(request):
    # Create lobby and store response in memory
    response = create_lobby()
    return web.json_response(response)


async def join_lobby_request(request):
    # Create lobby and store response in memory
    response = join_lobby()
    return web.json_response(response)


async def leave_lobby_request(request):
    # Create lobby and store response in memory
    response = leave_lobby()
    return web.json_response(response)

async def repl( websocket ):
    websockets_connected.add(websocket)
    async for message in websocket:
        try:
            incoming = LiveAPIEvent()
            incoming.ParseFromString(message)
            print( incoming )
        except websockets.exceptions.ConnectionClosedError:
            # Explicitly ignoring 'ConnectionClosedError' exceptions.
            pass
        except:
            print( message )


# set up web server
async def main():
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_get('/create_lobby', create_lobby_request)
    app.router.add_get('/join_lobby', join_lobby_request)
    app.router.add_get('/leave_lobby', leave_lobby_request)
    app.router.add_get('/send_chat', send_chat_request)
    app.router.add_post('/send_chat', send_chat_request)
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('.'))
    web_runner = web.AppRunner(app)

    await web_runner.setup()
    site = web.TCPSite(web_runner, 'localhost', 8000)
    await site.start()
    
    async with websockets.serve(repl, "localhost", 7777):
        await asyncio.Future()  # run forever on port 7777

@aiohttp_jinja2.template('index.html')
async def index(request):
    return {}


asyncio.run(main())