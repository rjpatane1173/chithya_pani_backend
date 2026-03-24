from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Room, Player, RoundAction
from .serializers import CreateRoomSerializer, StartGameSerializer
from .utils import generate_room_code
from .role_utils import assign_roles


@api_view(['POST'])
def create_room(request):

    serializer = CreateRoomSerializer(data=request.data)

    if serializer.is_valid():

        name = serializer.validated_data['name']
        number_of_players = serializer.validated_data['number_of_players']
        target_score = serializer.validated_data['target_score']

        while True:
            room_code = generate_room_code()
            if not Room.objects.filter(room_code=room_code).exists():
                break

        room = Room.objects.create(
            room_code=room_code,
            number_of_players=number_of_players,
            target_score=target_score
        )

        player = Player.objects.create(
            room=room,
            name=name,
            is_host=True
        )

        return Response({
            "room_code": room.room_code,
            "player_id": player.id,
            "is_host": True
        })

    return Response(serializer.errors)
from .serializers import JoinRoomSerializer


@api_view(['POST'])
def join_room(request):
    serializer = JoinRoomSerializer(data=request.data)

    if serializer.is_valid():
        name = serializer.validated_data['name']
        room_code = serializer.validated_data['room_code']

        try:
            room = Room.objects.get(room_code=room_code)
        except Room.DoesNotExist:
            return Response({"error": "Room not found"}, status=404)

        if room.status != "WAITING":
            return Response({"error": "Game already started"}, status=400)

        player_count = Player.objects.filter(room=room).count()

        if player_count >= room.number_of_players:
            return Response({"error": "Room is full"}, status=400)

        # --- ADD THIS NEW CHECK HERE ---
        # Check if the name already exists in this specific room (case-insensitive)
        if Player.objects.filter(room=room, name__iexact=name).exists():
            return Response({"error": "Name already taken! Please choose another."}, status=400)
        # -------------------------------

        player = Player.objects.create(
            room=room,
            name=name
        )

        return Response({
            "player_id": player.id,
            "room_code": room.room_code,
            "name": player.name
        })

    return Response(serializer.errors)

@api_view(['GET'])
def get_room(request, room_code):
    try:
        room = Room.objects.get(room_code=room_code)
    except Room.DoesNotExist:
        return Response({"error": "Room not found"}, status=404)

    players = Player.objects.filter(room=room)

    player_list = []
    for player in players:
        player_list.append({
            "id": player.id,
            "name": player.name,
            "is_host": player.is_host,
            "role": player.role,
            "score": player.score
        })

    # --- ADD THIS NEW BLOCK ---
    # Fetch the police's final guess if the round has ended
    police_target_id = None
    if room.round_ended:
        police_guess = RoundAction.objects.filter(
            room=room,
            round_number=room.current_round,
            action_type="POLICE_GUESS"
        ).first()
        
        if police_guess:
            police_target_id = police_guess.target_player.id
    # --------------------------

    return Response({
        "room_code": room.room_code,
        "target_score": room.target_score,
        "number_of_players": room.number_of_players,
        "players_joined": players.count(),
        "status": room.status,
        "current_round": room.current_round,
        "round_ended": room.round_ended,
        "police_target_id": police_target_id,  # <--- AND ADD THIS LINE
        "players": player_list
    })

@api_view(['POST'])
def start_game(request):

    serializer = StartGameSerializer(data=request.data)

    if serializer.is_valid():

        room_code = serializer.validated_data['room_code']
        player_id = serializer.validated_data['player_id']

        try:
            room = Room.objects.get(room_code=room_code)
        except Room.DoesNotExist:
            return Response({"error": "Room not found"}, status=404)

        try:
            player = Player.objects.get(id=player_id, room=room)
        except Player.DoesNotExist:
            return Response({"error": "Player not found in this room"}, status=404)

        # Check if player is host
        if not player.is_host:
            return Response({"error": "Only host can start the game"}, status=403)

        # Check if already started
        if room.status != "WAITING":
            return Response({"error": "Game already started"}, status=400)

        # Check if room is full
        player_count = Player.objects.filter(room=room).count()

        if player_count != room.number_of_players:
            return Response({
                "error": "Cannot start game. Waiting for all players to join.",
                "players_joined": player_count,
                "required": room.number_of_players
            }, status=400)

        # Start game
        room.status = "RUNNING"
        room.save()

        # Assign roles
        assign_roles(room)

        return Response({
            "message": "Game started successfully",
            "room_code": room.room_code,
            "status": room.status
        })

    return Response(serializer.errors)

@api_view(['GET'])
def get_my_role(request):

    player_id = request.GET.get('player_id')
    room_code = request.GET.get('room_code')

    try:
        room = Room.objects.get(room_code=room_code)
    except Room.DoesNotExist:
        return Response({"error": "Room not found"}, status=404)

    try:
        player = Player.objects.get(id=player_id, room=room)
    except Player.DoesNotExist:
        return Response({"error": "Player not found"}, status=404)

    return Response({
        "player_id": player.id,
        "name": player.name,
        "role": player.role
    })

@api_view(['GET'])
def get_police(request):

    room_code = request.GET.get('room_code')

    try:
        room = Room.objects.get(room_code=room_code)
    except Room.DoesNotExist:
        return Response({"error": "Room not found"}, status=404)

    police_players = Player.objects.filter(room=room, role="POLICE")

    police_list = []

    for p in police_players:
        police_list.append({
            "id": p.id,
            "name": p.name
        })

    return Response({
        "room_code": room.room_code,
        "police": police_list
    })

@api_view(['POST'])
def next_round(request):
    room_code = request.data.get('room_code')
    player_id = request.data.get('player_id')
    
    room = Room.objects.get(room_code=room_code)
    player = Player.objects.get(id=player_id, room=room)
    
    if not player.is_host:
        return Response({"error": "Only host can start next round"}, status=403)
    
    # Increment round and reset round_ended
    room.current_round += 1
    room.round_ended = False  # Reset for new round
    room.save()
    
    # Reset roles
    from .role_utils import assign_roles
    assign_roles(room)
    
    return Response({
        "message": "Next round started",
        "round": room.current_round
    })

@api_view(['POST'])
def mark_suspect(request):
    player_id = request.data.get('player_id')
    target_id = request.data.get('target_id')
    room_code = request.data.get('room_code')

    room = Room.objects.get(room_code=room_code)
    player = Player.objects.get(id=player_id, room=room)
    target = Player.objects.get(id=target_id, room=room)

    # Only police can mark suspects
    if player.role != "POLICE":
        return Response({"error": "Only police can mark suspects"}, status=403)

    # Check if already marked by this police
    existing = RoundAction.objects.filter(
        room=room,
        round_number=room.current_round,
        player=player,
        action_type="SUSPECT",
        target_player=target
    ).first()

    if existing:
        # Unmark - delete the suspect mark
        existing.delete()
        return Response({"message": "Suspect unmarked", "action": "unmarked"})
    else:
        # Mark new suspect
        RoundAction.objects.create(
            room=room,
            round_number=room.current_round,
            player=player,
            action_type="SUSPECT",
            target_player=target
        )
        return Response({"message": "Suspect marked", "action": "marked"})
    
@api_view(['GET'])
def get_suspects(request):
    room_code = request.GET.get('room_code')
    room = Room.objects.get(room_code=room_code)
    
    suspects = RoundAction.objects.filter(
        room=room,
        round_number=room.current_round,
        action_type="SUSPECT"
    )
    
    result = []
    for s in suspects:
        result.append({
            "by": s.player.name,
            "by_id": s.player.id,  # Add player ID
            "target": s.target_player.name,
            "target_id": s.target_player.id  # Add target ID
        })
    
    return Response(result)

@api_view(['POST'])
def police_guess(request):

    player_id = request.data.get('player_id')
    target_id = request.data.get('target_id')
    room_code = request.data.get('room_code')

    room = Room.objects.get(room_code=room_code)
    player = Player.objects.get(id=player_id, room=room)
    target = Player.objects.get(id=target_id, room=room)

    if player.role != "POLICE":
        return Response({"error": "Only police can guess"}, status=403)

    # prevent duplicate selection
    existing = RoundAction.objects.filter(
        room=room,
        round_number=room.current_round,
        action_type="POLICE_GUESS",
        target_player=target
    )

    if existing.exists():
        return Response({"error": "Already selected"}, status=400)

    RoundAction.objects.create(
        room=room,
        round_number=room.current_round,
        player=player,
        action_type="POLICE_GUESS",
        target_player=target
    )

    return Response({"message": "Guess submitted"})

# @api_view(['POST'])
# def calculate_score(request):
#     room_code = request.data.get('room_code')
    
#     try:
#         room = Room.objects.get(room_code=room_code)
        
#         # Get the police guess for this round
#         police_guess = RoundAction.objects.filter(
#             room=room,
#             round_number=room.current_round,
#             action_type="POLICE_GUESS"
#         ).first()
        
#         if police_guess:
#             target = police_guess.target_player
            
#             # Check if target is thief
#             if target.role == "THIEF":
#                 # Police catch thief - add points to all police
#                 police_players = Player.objects.filter(room=room, role="POLICE")
#                 for police in police_players:
#                     police.score += 500
#                     police.save()
#             else:
#                 # Thief escapes - add points to thief
#                 thief = Player.objects.filter(room=room, role="THIEF").first()
#                 if thief:
#                     thief.score += 500
#                     thief.save()
        
#         # Mark round as ended
#         room.round_ended = True
#         room.save()
        
#         # Return updated scores in response
#         players = Player.objects.filter(room=room)
#         scores_data = {}
#         for player in players:
#             scores_data[player.id] = player.score
        
#         return Response({
#             "message": "Score calculated",
#             "scores": scores_data,
#             "round_ended": True
#         })
        
#     except Room.DoesNotExist:
#         return Response({"error": "Room not found"}, status=404)


######################################################################
######################################################################
###########Follwing works fine
######################################################################
######################################################################

# @api_view(['POST'])
# def calculate_score(request):
#     room_code = request.data.get('room_code')
    
#     try:
#         room = Room.objects.get(room_code=room_code)
        
#         # Get the police guess for this round
#         police_guess = RoundAction.objects.filter(
#             room=room,
#             round_number=room.current_round,
#             action_type="POLICE_GUESS"
#         ).first()
        
#         if police_guess:
#             target = police_guess.target_player
            
#             # Check if target is thief
#             if target.role == "THIEF":
#                 # Police catch thief - add points to all police
#                 police_players = Player.objects.filter(room=room, role="POLICE")
#                 for police in police_players:
#                     police.score += 500
#                     police.save()
                    
#                 # King gets 1000 points when thief is caught
#                 king = Player.objects.filter(room=room, role="KING").first()
#                 if king:
#                     king.score += 1000
#                     king.save()
                    
#                 # Queen gets 800 points when thief is caught
#                 queen = Player.objects.filter(room=room, role="QUEEN").first()
#                 if queen:
#                     queen.score += 800
#                     queen.save()
                    
#             else:
#                 # Thief escapes - add points to thief
#                 thief = Player.objects.filter(room=room, role="THIEF").first()
#                 if thief:
#                     thief.score += 500
#                     thief.save()
                    
#                 # King gets 1000 points when thief escapes? 
#                 # Or do they only get points when thief is caught?
#                 # Adjust based on your game rules
#                 king = Player.objects.filter(room=room, role="KING").first()
#                 if king:
#                     king.score += 1000  # Adjust if needed
#                     king.save()
                    
#                 # Queen gets 800 points when thief escapes?
#                 queen = Player.objects.filter(room=room, role="QUEEN").first()
#                 if queen:
#                     queen.score += 800  # Adjust if needed
#                     queen.save()
        
#         # Mark round as ended
#         room.round_ended = True
#         room.save()
        
#         # Return updated scores in response
#         players = Player.objects.filter(room=room)
#         scores_data = {}
#         for player in players:
#             scores_data[player.id] = player.score
        
#         return Response({
#             "message": "Score calculated",
#             "scores": scores_data,
#             "round_ended": True
#         })
        
#     except Room.DoesNotExist:
#         return Response({"error": "Room not found"}, status=404)

######################################################################
######################################################################
#########################YTRial
######################################################################
######################################################################

@api_view(['POST'])
def calculate_score(request):
    room_code = request.data.get('room_code')
    
    try:
        room = Room.objects.get(room_code=room_code)
        
        # Get the police guess for this round
        police_guess = RoundAction.objects.filter(
            room=room,
            round_number=room.current_round,
            action_type="POLICE_GUESS"
        ).first()
        
        if police_guess:
            target = police_guess.target_player
            
            # Check if target is thief
            if target.role == "THIEF":
                # Police catch thief - add points to all police
                police_players = Player.objects.filter(room=room, role="POLICE")
                for police in police_players:
                    police.score += 500
                    police.save()
                    
                # King gets 1000 points when thief is caught
                king = Player.objects.filter(room=room, role="KING").first()
                if king:
                    king.score += 1000
                    king.save()
                    
                # Queen gets 800 points when thief is caught
                queen = Player.objects.filter(room=room, role="QUEEN").first()
                if queen:
                    queen.score += 800
                    queen.save()
                
                # Thief loses 250 points when caught (can't go below 0)
                thief = Player.objects.filter(room=room, role="THIEF").first()
                if thief:
                    thief.score = max(0, thief.score - 250)
                    thief.save()
                    
            else:
                # Thief escapes - add points to thief
                thief = Player.objects.filter(room=room, role="THIEF").first()
                if thief:
                    thief.score += 500
                    thief.save()
        
        # Mark round as ended
        room.round_ended = True
        room.save()
        
        # Return updated scores in response
        players = Player.objects.filter(room=room)
        scores_data = {}
        for player in players:
            scores_data[player.id] = player.score
        
        return Response({
            "message": "Score calculated",
            "scores": scores_data,
            "round_ended": True
        })
        
    except Room.DoesNotExist:
        return Response({"error": "Room not found"}, status=404)

@api_view(['GET'])
def check_player(request):
    player_id = request.GET.get('player_id')
    room_code = request.GET.get('room_code')
    
    try:
        room = Room.objects.get(room_code=room_code)
        player = Player.objects.get(id=player_id, room=room)
        
        return Response({
            "is_valid": True,
            "player_id": player.id,
            "name": player.name,
            "is_host": player.is_host
        })
        
    except (Room.DoesNotExist, Player.DoesNotExist):
        return Response({
            "is_valid": False,
            "error": "Player not found in this room"
        }, status=404)