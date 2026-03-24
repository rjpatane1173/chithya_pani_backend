from rest_framework import serializers

class CreateRoomSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)
    number_of_players = serializers.IntegerField()
    target_score = serializers.IntegerField()

    def validate_number_of_players(self, value):
        if value < 4 or value > 12:
            raise serializers.ValidationError("Players must be between 4 and 12")
        return value

    def validate_target_score(self, value):
        if value not in [5000, 10000, 15000, 20000]:
            raise serializers.ValidationError("Invalid target score")
        return value
    
class JoinRoomSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)
    room_code = serializers.CharField(max_length=5)

class StartGameSerializer(serializers.Serializer):
    room_code = serializers.CharField(max_length=5)
    player_id = serializers.IntegerField()