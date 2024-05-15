import random
from uuid import UUID

from aredis_om import NotFoundError

from ibg.api.models.error import (
    CantVoteBecauseYouDeadError,
    CantVoteForDeadPersonError,
    CantVoteForYourselfError,
    GameNotFoundError,
    RoomNotFoundError,
)
from ibg.api.models.event import EventCreate
from ibg.api.models.game import GameCreate, GameType
from ibg.api.models.table import Game, Room
from ibg.api.models.undercover import UndercoverRole, Word
from ibg.socketio.models.room import Room as RedisRoom
from ibg.socketio.models.shared import IBGSocket
from ibg.socketio.models.socket import StartGame, StartNewTurn, UndercoverGame, UndercoverTurn, VoteForAPerson
from ibg.socketio.models.user import UndercoverSocketPlayer
from ibg.socketio.routers.shared import send_event_to_client, socketio_exception_handler


def undercover_events(sio: IBGSocket) -> None:

    async def _start_new_turn(db_room: Room, db_game: Game, redis_game: UndercoverGame) -> None:
        """
        Start a new turn in the game. If the room or game does not exist, raise a RoomNotFoundError or GameNotFoundError.

        :param start_new_turn_data: The data to start a new turn.
        :return: None
        """
        turn = sio.game_controller.create_turn(game_id=db_game.id)
        sio.game_controller.create_turn_event(
            game_id=db_game.id,
            event_create=EventCreate(
                name="start_turn",
                data={
                    "game_id": db_game.id,
                    "turn_id": turn.id,
                    "message": f"Turn {turn.id} started.",
                },
                user_id=db_room.owner_id,
            ),
        )
        redis_game.turns.append(UndercoverTurn())
        await redis_game.save()

    async def _get_civilian_and_undercover_words() -> tuple[Word, Word]:
        """
        Get the civilian and undercover words for the game.

        :param game_id: The id of the game.
        :return: tuple[str, str]
        """
        term_pair = await sio.undercover_controller.get_random_term_pair()
        civilian_word_id = term_pair.word1_id
        undercover_word_id = term_pair.word2_id
        if random.choice([True, False]):
            civilian_word_id, undercover_word_id = (
                term_pair.word2_id,
                term_pair.word1_id,
            )
        civilian_word = await sio.undercover_controller.get_word_by_id(civilian_word_id)
        undercover_word = await sio.undercover_controller.get_word_by_id(undercover_word_id)
        return civilian_word, undercover_word

    async def _create_undercover_game(
        start_game_input: StartGame,
    ) -> tuple[Game, UndercoverGame]:
        """
        Create an undercover game, assign roles to players, and save the game to the Redis database.

        :param start_game_input: The input to start the game.
        :return: The created undercover game.
        """
        db_room = await sio.room_controller.get_room_by_id(start_game_input.room_id)
        try:
            room = await RedisRoom.find(RedisRoom.id == str(db_room.id)).first()
        except NotFoundError:
            raise RoomNotFoundError(room_id=start_game_input.room_id)
        players = room.users
        num_players = len(players)
        num_mr_white = 1 if num_players < 10 else (2 if num_players <= 15 else 3)
        num_undercover = max(2, num_players // 4)
        num_civilians = num_players - num_mr_white - num_undercover
        roles = (
            [UndercoverRole.UNDERCOVER] * num_undercover
            + [UndercoverRole.CIVILIAN] * num_civilians
            + [UndercoverRole.MR_WHITE] * num_mr_white
        )
        random.shuffle(roles)
        undercover_players = [
            UndercoverSocketPlayer(user_id=player.id, username=player.username, role=role, sid=player.sid)
            for player, role in zip(players, roles)
        ]
        undercover_players[random.randint(0, len(undercover_players) - 1)].is_mayor = True
        civilian_word, undercover_word = await _get_civilian_and_undercover_words()
        db_game = await sio.game_controller.create_game(
            GameCreate(
                room_id=db_room.id,
                number_of_players=len(players),
                type=GameType.UNDERCOVER,
                game_configurations={
                    "civilian_word": civilian_word.word,
                    "undercover_word": undercover_word.word,
                    "civilian_word_id": str(civilian_word.id),
                    "undercover_word_id": str(undercover_word.id),
                },
            )
        )
        redis_game = UndercoverGame(
            civilian_word=civilian_word.word,
            undercover_word=undercover_word.word,
            room_id=str(db_room.id),
            id=str(db_game.id),
            players=undercover_players,
        )
        await redis_game.save()
        await _start_new_turn(db_room, db_game, redis_game)
        return db_game, redis_game

    @sio.event
    @socketio_exception_handler(sio)
    async def start_undercover_game(sid, data) -> None:
        """
        SIO Event to start an Undercover Game in a Room with the given data.

        :param sid: The socket id of the user.
        :param data: Should match the StartGame model.
        :return: None
        """

        # Validation
        start_game_input = StartGame(**data)

        # Function Logic
        db_game, redis_game = await _create_undercover_game(start_game_input)

        # Send Notification to each player to assign role
        for player in redis_game.players:
            if player.role == UndercoverRole.MR_WHITE:
                await send_event_to_client(
                    sio,
                    "role_assigned",
                    {
                        "role": player.role.value,
                        "word": "You are Mr. White. You have to guess the word.",
                    },
                    room=player.sid,
                )
            else:
                word = (
                    redis_game.undercover_word if player.role == UndercoverRole.UNDERCOVER else redis_game.civilian_word
                )
                await send_event_to_client(
                    sio,
                    "role_assigned",
                    {
                        "role": player.role.value,
                        "word": word,
                    },
                    room=player.sid,
                )

        # Send Notification to Room that game has started
        await send_event_to_client(
            sio,
            "game_started",
            {
                "message": "Undercover Game has started. Check your role and word.",
                "players": [player.username for player in redis_game.players],
                "mayor": next(player.username for player in redis_game.players if player.is_mayor),
            },
            room=str(db_game.room.public_id),
        )

    @sio.event
    @socketio_exception_handler(sio)
    async def start_new_turn(sid, data) -> None:
        """
        Start a new turn in the game. If the room or game does not exist, raise a RoomNotFoundError or GameNotFoundError.

        :param sid: The socket id of the user.
        :param data: Should match the StartNewTurn model.
        :return: None
        """

        # Validation
        start_new_turn_data = StartNewTurn(**data)

        # Function Logic
        await _start_new_turn(start_new_turn_data)

        # Send Notification to Room that a new turn has started
        await send_event_to_client(
            sio,
            "notification",
            {"message": "Starting a new turn."},
            room=start_new_turn_data.room_id,
        )

    async def _eliminate_player_based_on_votes(
        game: UndercoverGame,
    ) -> tuple[UndercoverSocketPlayer, int]:
        """
        Eliminate the player with the most votes in the game.

        :param game: The game to eliminate the player from.
        :return: None
        """
        votes = game.turns[-1].votes
        vote_counts = {player.user_id: 0 for player in game.players}
        for voted_id in votes.values():
            vote_counts[voted_id] += 1

        # Get the player with the most votes
        max_votes = max(vote_counts.values())
        players_with_max_votes = [player_id for player_id, vote_count in vote_counts.items() if vote_count == max_votes]

        # If there is a tie, check if the mayor's vote can break the tie
        if len(players_with_max_votes) > 1:
            mayor_vote = next(
                (votes[player.user_id] for player in game.players if player.is_mayor),
                None,
            )
            if mayor_vote in players_with_max_votes:
                player_with_most_vote = mayor_vote
            else:
                player_with_most_vote = players_with_max_votes[
                    0
                ]  # If mayor's vote doesn't break the tie, choose the first player
        else:
            player_with_most_vote = players_with_max_votes[0]

        eliminated_player = next(player for player in game.players if player.user_id == player_with_most_vote)
        game.eliminated_players.append(eliminated_player)
        await game.save()

        return eliminated_player, vote_counts[player_with_most_vote]

    async def _set_vote(
        game: UndercoverGame, data: VoteForAPerson
    ) -> tuple[UndercoverSocketPlayer, UndercoverSocketPlayer]:
        """
        Get the player that is voting and the player that is voted for.

        :param game: The game to get the players from.
        :param data: The data to get the players from.
        :return: tuple[UndercoverSocketPlayer, UndercoverSocketPlayer]
        """
        player_to_vote: UndercoverSocketPlayer = next(
            player for player in game.players if player.user_id == data.user_id
        )
        if player_to_vote.is_alive is False:
            raise CantVoteBecauseYouDeadError(user_id=data.user_id)
        voted_player: UndercoverSocketPlayer = next(
            player for player in game.players if player.user_id == data.voted_user_id
        )
        if voted_player.is_alive is False:
            raise CantVoteForDeadPersonError(
                user_id=data.user_id,
                dead_user_id=data.voted_user_id,
            )
        if player_to_vote.user_id == voted_player.user_id:
            raise CantVoteForYourselfError(user_id=data.user_id)
        game.turns[-1].votes[UUID(data.user_id)] = voted_player.user_id
        await game.save()
        return player_to_vote, voted_player

    async def _check_if_a_team_has_win(game: UndercoverGame) -> UndercoverRole | None:
        """
        Check if a team has won the game. If the undercovers have won, return UndercoverRole.UNDERCOVER.
        If the civilians have won, return UndercoverRole.CIVILIAN.
        If the game is not over, return None.

        :param game: The game to check if a team has won.
        :return: UndercoverRole | None
        """
        num_alive_undercover = len(
            [player for player in game.players if player.role == UndercoverRole.UNDERCOVER and player.is_alive]
        )
        num_alive_civilian = len(
            [player for player in game.players if player.role == UndercoverRole.CIVILIAN and player.is_alive]
        )
        num_alive_mr_white = len(
            [player for player in game.players if player.role == UndercoverRole.MR_WHITE and player.is_alive]
        )
        if num_alive_undercover == 0 and num_alive_mr_white == 0:
            return UndercoverRole.CIVILIAN
        if num_alive_civilian == 0 or num_alive_mr_white == 0:
            return UndercoverRole.UNDERCOVER

    @sio.event
    @socketio_exception_handler(sio)
    async def vote_for_a_player(sid, data) -> None:
        """
        Vote for a player in the game. If the player is already dead, raise an Exception.
        If all players have voted, eliminate the player with the most votes.

        :param sid: The socket id of the user.
        :param data: Should match the VoteForAPerson model.
        :return: None
        """
        data = VoteForAPerson(**data)
        try:
            game = await UndercoverGame.find(UndercoverGame.id == data.game_id).first()
        except NotFoundError:
            raise GameNotFoundError(game_id=data.game_id)
        player_to_vote, voted_player = await _set_vote(game, data)
        if len(game.turns[-1].votes) == len(game.players) - len(game.eliminated_players):
            eliminated_player, number_of_vote = await _eliminate_player_based_on_votes(game)

            # Send Notification to Room that a player has been eliminated
            await send_event_to_client(
                sio,
                "player_eliminated",
                {
                    "message": f"Player {eliminated_player.username} is eliminated with {number_of_vote} votes against him.",
                    "eliminated_player_role": eliminated_player.role,
                },
                room=data.room_id,
            )

            # Send Notification to the eliminated player
            await send_event_to_client(
                sio,
                "you_died",
                {"message": f"You have been eliminated with {number_of_vote} votes against you."},
                room=eliminated_player.sid,
            )
            team_that_won = await _check_if_a_team_has_win(game)
            if team_that_won == UndercoverRole.CIVILIAN:
                await send_event_to_client(
                    sio,
                    "game_over",
                    {
                        "data": "The civilians have won the game.",
                    },
                    room=game.room_id,
                )
            elif team_that_won == UndercoverRole.UNDERCOVER:
                await send_event_to_client(
                    sio,
                    "game_over",
                    {
                        "data": "The undercovers have won the game.",
                    },
                    room=game.room_id,
                )

        else:
            players_that_voted = [player for player in game.players if player.id in game.turns[-1].votes.values()]
            await send_event_to_client(
                sio,
                "vote_casted",
                {
                    "message": "Vote casted.",
                },
                room=sid,
            )
            await send_event_to_client(
                sio,
                "waiting_other_votes",
                {
                    "message": "Waiting for other players to vote.",
                    "players_that_voted": [
                        {
                            "username": player.username,
                            "user_id": str(player.user_id),
                        }
                        for player in players_that_voted
                    ],
                },
                room=sid,
            )
