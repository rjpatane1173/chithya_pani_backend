from django.db import models
import uuid


class Room(models.Model):
    room_code = models.CharField(max_length=5, unique=True)
    number_of_players = models.IntegerField()
    target_score = models.IntegerField()
    status = models.CharField(max_length=20, default="WAITING")
    current_round = models.IntegerField(default=1)
    round_ended = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.room_code
    

###########################################################################
# This following is used to just create player  
# class Player(models.Model):
#     room = models.ForeignKey(Room, on_delete=models.CASCADE)
#     name = models.CharField(max_length=50)
#     is_host = models.BooleanField(default=False)
#     score = models.IntegerField(default=0)
#     joined_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.name

ROLE_CHOICES = [
    ("KING", "King"),
    ("QUEEN", "Queen"),
    ("POLICE", "Police"),
    ("THIEF", "Thief"),
    ("CITIZEN", "Citizen"),
]


class Player(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    is_host = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    ####################

class RoundAction(models.Model):
    ACTION_CHOICES = [
        ("SUSPECT", "Suspect"),
        ("POLICE_GUESS", "Police Guess"),
        ("THIEF_TARGET", "Thief Target"),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    round_number = models.IntegerField()
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="target")

    created_at = models.DateTimeField(auto_now_add=True)