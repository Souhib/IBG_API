from fastapi import APIRouter
from starlette.responses import HTMLResponse

from ibg.api.models.room import RoomCreate
from ibg.api.models.view import RoomView
from ibg.socketio.models.room import JoinRoomUser, LeaveRoomUser
from ibg.socketio.models.shared import IBGSocket
from ibg.socketio.routers.shared import send_event_to_client, serialize_model, socketio_exception_handler

router = APIRouter(
    responses={404: {"description": "Not found"}},
)


test = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Socket.IO Room Management</title>
    <script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>
    <script>
    document.addEventListener('DOMContentLoaded', () => {
        const urlParams = new URLSearchParams(window.location.search);
        const user_id = urlParams.get('user_id') || generateUUID();
        const room_id = urlParams.get('room_id') || generateUUID();
        const sid = urlParams.get('sid') || generateUUID();

        const socket = io('http://127.0.0.1:5000/');
        const joinRoomButton = document.getElementById('joinRoom');
        const createRoomButton = document.getElementById('createRoom');
        const leaveRoomButton = document.getElementById('leaveRoom');
        const startGameButton = document.getElementById('startGame');
        const voteButton = document.getElementById('voteButton');
        const roomInput = document.getElementById('roomInput');
        const passwordInput = document.getElementById('passwordInput');
        const playersSelect = document.getElementById('playersSelect');

        function generateUUID() {
            return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
                (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
            );
        }

        joinRoomButton.addEventListener('click', () => {
            const room = roomInput.value || room_id;
            const password = passwordInput.value;
            console.log(`User ID: ${user_id}`);
            socket.emit('join_room', {
                public_room_id: room,
                user_id: user_id,
                password: password
            });
            console.log(`Requested to join room ${room}`);
        });

        createRoomButton.addEventListener('click', () => {
            // const room = roomInput.value || room_id;
            const password = passwordInput.value;
            socket.emit('create_room', {
                owner_id: user_id,
                status: 'online',
                password: password
            });
            console.log(`Requested to create and join room with password ${password}`);
        });

        leaveRoomButton.addEventListener('click', () => {
            const room = roomInput.value || room_id;
            socket.emit('leave_room', {
                room_id: room,
                user_id: user_id,
            });
            console.log(`Requested to leave room ${room}`);
        });

        startGameButton.addEventListener('click', () => {
            const room = roomInput.value || room_id;
            socket.emit('start_undercover_game', {
                room_id: room,
                user_id: user_id
            });
            console.log(`Requested to start game in room ${room}`);
        });

        voteButton.addEventListener('click', () => {
            const voted_user_id = playersSelect.value;
            if (voted_user_id) {
                socket.emit('vote_for_a_player', {
                    user_id: user_id,
                    voted_user_id: voted_user_id,
                    game_id: room_id,
                });
                console.log(`Voted for player ${voted_user_id}`);
            } else {
                console.log('No player selected to vote for.');
            }
        });

        socket.on('room_status', (data) => {
            console.log(data.data);
            document.getElementById('status').textContent = data.data;
        });

        socket.on('notification', (data) => {
            console.log(data.data);
            const messages = document.getElementById('messages');
            messages.textContent += `${data.data}\n`;
        });

        socket.on('game_started', (data) => {
            console.log('Game started:', data);
            let players = data.players;
            playersSelect.innerHTML = '';
            players.forEach(player => {
                if (player !== user_id) {
                    let option = new Option(player, player);
                    playersSelect.add(option);
                }
            });
            document.getElementById('votingSection').style.display = 'block';
        });
    });
    </script>
</head>
<body>
    <h1>Socket.IO Room Management</h1>
    <input type="text" id="roomInput" placeholder="Room ID">
    <input type="password" id="passwordInput" placeholder="Room Password">
    <button id="joinRoom">Join Room</button>
    <button id="createRoom">Create Room</button>
    <button id="leaveRoom">Leave Room</button>
    <button id="startGame">Start Game</button>
    <div id="status"></div>
    <pre id="messages"></pre>
    <div id="votingSection" style="display:none;">
        <h2>Vote for a Player</h2>
        <select id="playersSelect">
            <option value="">Select a player to vote for</option>
        </select>
        <button id="voteButton">Vote</button>
    </div>
</body>
</html>
"""


@router.get("/site", response_class=HTMLResponse)
def get_website():
    return HTMLResponse(content=test, status_code=200)


def room_events(sio: IBGSocket) -> None:

    @sio.event
    @socketio_exception_handler(sio)
    async def join_room(sid, data) -> None:
        # Validation
        join_room_user = JoinRoomUser(**data)

        # Function Logic
        room = await sio.socket_room_controller.user_join_room(sid, join_room_user)
        await sio.enter_room(sid=sid, room=room.public_id)

        room_view = serialize_model(RoomView.model_validate(room))

        # Send Notification to the user that they have joined
        await send_event_to_client(
            sio,
            "room_status",
            {
                "user_id": str(join_room_user.user_id),
                "username": room.users[-1].username,
                "message": f"You joined the room {room.public_id}.",
                "data": room_view,
            },
            room=sid,
        )

        # Send Notification to Room that user has joined
        await send_event_to_client(
            sio,
            "new_user_joined",
            {
                "user_id": str(join_room_user.user_id),
                "username": room.users[-1].username,
                "message": f"User {sid} has joined the room.",
                "data": room_view,
            },
            room=str(room.public_id),
        )

    @sio.event
    @socketio_exception_handler(sio)
    async def create_room(sid, data) -> None:
        # Validation
        create_room_user = RoomCreate(**data)

        # Function Logic
        room = await sio.socket_room_controller.create_room(sid, create_room_user)
        await sio.enter_room(sid, room.public_id)

        room_view = serialize_model(RoomView.model_validate(room))

        # Send Notification to the user that they have joined
        await send_event_to_client(
            sio,
            "new_room_created",
            {"message": f"Room {room.id} created.", "data": room_view},
            room=sid,
        )

    @sio.event
    @socketio_exception_handler(sio)
    async def leave_room(sid, data) -> None:
        # Validation
        leave_room_user = LeaveRoomUser(**data)

        # Function Logic
        room = await sio.socket_room_controller.user_leave_room(leave_room_user)
        await sio.leave_room(sid, leave_room_user.room_id)

        # Send Notification to the user that they have left
        await send_event_to_client(
            sio,
            "you_left",
            {
                "user_id": str(leave_room_user.user_id),
                "username": leave_room_user.username,
                "message": f"You left the room {leave_room_user.room_id}.",
            },
            room=sid,
        )

        # Send Notification to Room that user has left
        await send_event_to_client(
            sio,
            "user_left",
            {
                "user_id": str(leave_room_user.user_id),
                "username": leave_room_user.username,
                "message": f"User {leave_room_user.username} has left the room.",
                "data": serialize_model(RoomView.model_validate(room)),
            },
            room=str(leave_room_user.room_id),
        )
