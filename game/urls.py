from django.urls import path
from .views import create_room, join_room, get_room, start_game, get_my_role, get_police, next_round, mark_suspect, get_suspects, police_guess, calculate_score, check_player

urlpatterns = [
    path('create-room/', create_room),
    path('join-room/', join_room),
    path('room/<str:room_code>/', get_room),
    path('start-game/', start_game),
    path('my-role/', get_my_role),
    path('police/', get_police),
    path('next-round/', next_round),
    path('suspect/', mark_suspect),
    path('suspects/', get_suspects),
    path('police-guess/', police_guess),
    path('calculate-score/', calculate_score),
    path('api/check-player/', check_player, name='check-player'),
]