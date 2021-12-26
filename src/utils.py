from django.http import HttpResponse


def check_user_is_room_owner(request, room):
    if request.user != room.host:
        return HttpResponse("Not allowed!")


def check_user_is_message_sender(request, message):
    if request.user != message.user:
        return HttpResponse("Not allowed!")
