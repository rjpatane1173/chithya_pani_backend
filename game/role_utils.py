import random
from .models import Player


def get_roles(player_count):

    if player_count == 4:
        roles = ["KING", "QUEEN", "POLICE", "THIEF"]

    elif player_count in [5, 6]:
        roles = ["KING", "QUEEN", "POLICE", "THIEF", "THIEF", "CITIZEN"]

    elif player_count in [7, 8]:
        roles = ["KING", "QUEEN", "POLICE", "POLICE", "THIEF", "THIEF", "CITIZEN", "CITIZEN"]

    elif player_count in [9, 10]:
        roles = ["KING", "QUEEN", "POLICE", "POLICE", "POLICE", "THIEF", "THIEF", "THIEF", "CITIZEN", "CITIZEN"]

    elif player_count in [11, 12]:
        roles = ["KING", "QUEEN", "POLICE", "POLICE", "POLICE", "POLICE", "THIEF", "THIEF", "THIEF", "THIEF", "CITIZEN", "CITIZEN"]

    else:
        roles = []

    random.shuffle(roles)
    return roles



def assign_roles(room):

    players = list(Player.objects.filter(room=room))
    player_count = len(players)

    roles = get_roles(player_count)

    for player, role in zip(players, roles):
        player.role = role
        player.save()