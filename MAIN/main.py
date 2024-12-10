import asyncio
import websockets
import json
import os
from urllib.parse import urlparse, parse_qs
import signal
import time

import lang
import jsonLoader
import validator
import sqlite_handler as sqlh
import key

os.chdir(os.path.dirname(os.path.abspath(__file__)))

################################
# NEW CONFIG FILE
# IF THERES NONE
################################
def_config = {
    "ip": "localhost",
    "port": 443,
    "version": "1.0",
    "max-players": 10,
    "cross-origin": {"active": True, "domains": ["127.0.0.1", "localhost"]},
    "password-protected": {"active": False, "password": "password"},
    "discarded-close-codes": [3001, 4000, 4001],
    "lang": "EN",
}

language = any
version = any
maxplayers = any
cross_origin_active = any
cross_origin_domains = any
password_protected_active = any
password_protected_password = any
discarded_close_codes = any


################################
# LOAD CONFIG AND START SERVER
################################
async def main():
    global maxplayers, cross_origin_domains, cross_origin_active, password_protected_active, password_protected_password, discarded_close_codes, version
    await key.load_keys()
    config = await jsonLoader.load("config", def_config)
    language = config.get("lang")
    lang.loadLangFile(language)
    maxplayers = config.get("max-players")
    cross_origin_active = config["cross-origin"]["active"]
    cross_origin_domains = config["cross-origin"]["domains"]
    password_protected_active = config["password-protected"]["active"]
    password_protected_password = config["password-protected"]["password"]
    discarded_close_codes = config.get("discarded-close-codes")
    version = config.get("version")
    await sqlh.start()
    

    async with websockets.serve(handler, config.get("ip"), config.get("port")):
        print(
            lang.parse("ServerStart", [config.get("ip"), config.get("port"), version])
        )
        repeater_task = asyncio.create_task(repeater())  # Create the repeater task
        try:
            await asyncio.Future()  # Keep main running
            
            def signal_handler(sig, frame):
                loop = asyncio.get_running_loop()
                loop.stop()
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
        except asyncio.CancelledError:
            print(lang.parse("ServerStop", []))
            await asyncio.sleep(2)
            repeater_task.cancel()  # Cancel the repeater task when main exits


# All connected clients
connectedClients = set()

# All logged clients
clientToID = {}

# Current Lobby details
currentLobby = {
    "map": 0,
    "mode": 0,
    "teams": False, # If teams is false all player go to players list 
    "players": {}, # else they go to team_a or team_b
    "team_a": {}, # Empty if teams is false
    "team_b": {}, # Empty if teams is false
    "time": 0,
    "reset_time": 0,
    "team_score": [0, 0],
}
# In game Clients
inGameClients = set()


async def handler(websocket, path):
    global maxplayers, cross_origin_domains, cross_origin_active, password_protected_active, password_protected_password, discarded_close_codes, version
    try:
        ################################
        # CROSS ORIGIN IF ACTIVE
        ################################
        origin = websocket.request_headers.get("Origin", "undefined")
        if cross_origin_active and not validator.is_domain_authorized(
            origin, cross_origin_domains
        ):
            await websocket.close(3001, lang.message_parse("InvalidOrigin"))
        ################################
        # MAX PLAYERS
        ################################
        elif len(connectedClients.copy()) >= maxplayers:
            await websocket.close(4000, lang.message_parse("MaxConnectionsReached"))
        ################################
        # PASSWORD PROTECTED IF ACTIVE
        ################################
        else:
            query = urlparse(path).query
            params = parse_qs(query)
            connection_password = params.get("password", [""])[0]
            if (
                not password_protected_password == str(connection_password)
                and password_protected_active
            ):
                await websocket.close(
                    4001, lang.message_parse("ServerIsPasswordProtected")
                )
            else:
                await websocket.send(
                    json.dumps(
                        {
                            "type": "server",
                            "version": version,
                            "public-key": key.public_key_pem.decode(),
                        }
                    )
                )
                connectedClients.add(websocket)
                print(
                    lang.parse(
                        "Connect",
                        [
                            websocket.remote_address[0],  # IP
                            len(connectedClients),  # CurrentPlayers
                            maxplayers,  # MaxPlayers
                        ],
                    )
                )
        ################################
        # AWAIT ANY MESSAGE
        ################################
        while True:
            try:
                message = await websocket.recv()
                if websocket in connectedClients:
                    data = json.loads(message)
                    type_ = data.get("type")

                    if type_ == "register":
                        if clientToID.get(websocket) is not None:
                            await websocket.send(
                                json.dumps(
                                    {
                                        "type": "sign_response",
                                        "code": 2,
                                        "data": lang.message_parse("AlreadyLoggedIn"),
                                    }
                                )
                            )
                        else:
                            username = str(data.get("username", "e"))
                            password = str(data.get("password", "e"))
                            password = key.decrypt_data(password)
                            passlength = len(password)
                            password = validator.hash_password(
                                password
                            )  # Hash password
                            
                            if not validator.validUser(username) or passlength < 8 or passlength > 24:
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "type": "sign_response",
                                            "code": 5,
                                            "data": lang.message_parse(
                                                "UsernameOrPasswordInvalidLength"
                                            ),
                                        }
                                    )
                                )
                            elif username is None or password is None:
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "type": "sign_response",
                                            "code": 0,
                                            "data": lang.message_parse(
                                                "InvalidUsernameOrPassword"
                                            ),
                                        }
                                    )
                                )
                                continue
                            elif validator.validUser(username):
                                if not await sqlh.addUser(
                                    username, password
                                ):  # ADD USER AND CHECK IF USER ALREADY EXISTS
                                    await websocket.send(
                                        json.dumps(
                                            {
                                                "type": "sign_response",
                                                "code": 3,
                                                "data": lang.message_parse(
                                                    "UserAlreadyExists"
                                                ),
                                            }
                                        )
                                    )
                                else:
                                    clientToID[websocket] = (
                                        await sqlh.getUserIDFromName(username)
                                    )
                                    await websocket.send(
                                        json.dumps(
                                            {
                                                "type": "sign_response",
                                                "code": 1,
                                                "data": lang.message_parse("OK"),
                                            }
                                        )
                                    )
                                    await websocket.send(
                                        json.dumps(
                                            {
                                                "type": "profile_info",
                                                "data": f"{await sqlh.getDataFromID((clientToID[websocket]))}",
                                            }
                                        )
                                    )
                            else:
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "type": "sign_response",
                                            "code": 0,
                                            "data": lang.message_parse(
                                                "InvalidUsernameOrPassword"
                                            ),
                                        }
                                    )
                                )
                    if type_ == "login":
                        if (clientToID.get(websocket)) is not None:
                            await websocket.send(
                                json.dumps(
                                    {
                                        "type": "sign_response",
                                        "code": 2,
                                        "data": lang.message_parse("AlreadyLoggedIn"),
                                    }
                                )
                            )
                        else:
                            username = str(data.get("username", "e"))
                            password = str(data.get("password", "e"))
                            password = key.decrypt_data(password)
                            passlength = len(password)
                            id_fromUser = await sqlh.getUserIDFromName(username)
                            if not validator.validUser(username) or passlength < 8 or passlength > 24:
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "type": "sign_response",
                                            "code": 5,
                                            "data": lang.message_parse(
                                                "UsernameOrPasswordInvalidLength"
                                            ),
                                        }
                                    )
                                )
                            elif (
                                username is None
                                or password is None
                                or id_fromUser is False
                            ):
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "type": "sign_response",
                                            "code": 0,
                                            "data": lang.message_parse(
                                                "InvalidUsernameOrPassword"
                                            ),
                                        }
                                    )
                                )
                            elif await validator.verify_password(id_fromUser, password):
                                clientToID[websocket] = id_fromUser
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "type": "sign_response",
                                            "code": 1,
                                            "data": lang.message_parse("OK"),
                                        }
                                    )
                                )
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "type": "profile_info",
                                            "data": f"{await sqlh.getDataFromID((clientToID[websocket]))}",
                                        }
                                    )
                                )
                            else:
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "type": "sign_response",
                                            "code": 0,
                                            "data": lang.message_parse(
                                                "InvalidUsernameOrPassword"
                                            ),
                                        }
                                    )
                                )
                    if type_ == "ping":
                        server_timestamp = time.time() * 1000
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "pong",
                                    "code": 0,
                                    "data": server_timestamp,
                                }
                            )
                        )
                    if type_ == "enter_game":
                        if clientToID.get(websocket) is not None:
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "type": "game_response",
                                            "code": 1,
                                            "data": lang.message_parse("OK"),
                                        }
                                    )
                                )
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "type": "game_info",
                                            "data": f"{currentLobby}",
                                        }
                                    )
                                )
                            
                        else:
                            await websocket.send(
                                json.dumps(
                                    {
                                        "type": "sign_response",
                                        "code": 4,
                                        "data": lang.message_parse(
                                            "YouAreNotLoggedIn"
                                        ),
                                    }
                                )
                            )
                    if type_ == "join":
                        if clientToID.get(websocket) is not None:
                            if websocket not in inGameClients:
                                inGameClients.add(websocket)
                                name = await sqlh.getUserFromID(clientToID[websocket])
                                currentLobby["players"][str(clientToID[websocket])] = {'name':name,'x': '0','y': '0','vx': '0','vy': '0','direction': '0'}
                            else:
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "type": "game_response",
                                            "code": 0,
                                            "data": lang.message_parse(
                                                "AlreadyInGame"
                                            ),
                                        }
                                    )
                                )
                        else:
                            await websocket.send(
                                json.dumps(
                                    {
                                        "type": "sign_response",
                                        "code": 4,
                                        "data": lang.message_parse(
                                            "YouAreNotLoggedIn"
                                        ),
                                    }
                                )
                            )
                    if type_ == "receive_packet":
                        if clientToID.get(websocket) is not None:
                            if websocket in inGameClients:
                                playerID = clientToID.get(websocket)
                                name = currentLobby["players"][f"{playerID}"]["name"]
                                x = data.get("x", currentLobby["players"][f"{playerID}"]["x"])
                                y = data.get("y", currentLobby["players"][f"{playerID}"]["y"])
                                vx = data.get("vx", 0)
                                vy = data.get("vy", 0)
                                direction = data.get("direction", currentLobby["players"][f"{playerID}"]["direction"])                                
                                currentLobby["players"][f"{playerID}"] = {'name': name,'x': str(x),'y': str(y),'vx': str(vx),'vy': str(vy),'direction': str(direction)}
                                
                            else:
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "type": "game_response",
                                            "code": 0,
                                            "data": lang.message_parse(
                                                "NotInGame"
                                            ),
                                        }
                                    )
                                )
                        else:
                            await websocket.send(
                                json.dumps(
                                    {
                                        "type": "sign_response",
                                        "code": 4,
                                        "data": lang.message_parse(
                                            "YouAreNotLoggedIn"
                                        ),
                                    }
                                )
                            )
            except websockets.ConnectionClosed:
                break
            except Exception as e:
                print(
                    lang.parse("UnexpectedError", [e]),
                )
                break
    ################################
    # WAIT FOR DISCONNECTIONS
    ################################
    finally:
        await handle_disconnect(websocket)


################################
# IF IN LIST WILL OUTPUT
# DATA TO PLAYERS ON THAT LIST
################################
async def repeater():
    while True:
        for websocket in inGameClients.copy():
            try:
                await websocket.send(
                    json.dumps(
                        {
                            "type": "packet",
                            "data": f"{currentLobby['players']}",
                        }
                    )
                )
            except websockets.ConnectionClosed:
                pass
            except Exception as e:
                print(
                    lang.parse("UnexpectedError", [e]),
                )
        await asyncio.sleep(0.025) # 40 TPS


################################
# HANDLES DISCONNECTS
################################
async def handle_disconnect(websocket):
    global maxplayers, discarded_close_codes
    if websocket in connectedClients:
        connectedClients.discard(websocket)
    if f"{clientToID.get(websocket)}" in currentLobby["players"]:
        currentLobby["players"].pop(f"{clientToID.get(websocket)}")
    if clientToID.get(websocket) is not None:
        clientToID.pop(websocket)
    if websocket in inGameClients:
        inGameClients.discard(websocket)
    await websocket.close(1000, "Disconnected")
    if websocket.close_code not in discarded_close_codes:
        print(
            lang.parse(
                "Disconnect",
                [websocket.remote_address[0], len(connectedClients), maxplayers],
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
