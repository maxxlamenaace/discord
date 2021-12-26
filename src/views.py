from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q

from .models import Room, Topic, Message
from .forms import RoomForm
from .utils import check_user_is_room_owner, check_user_is_message_sender

# Create your views here.


def auth(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username").lower()
        password = request.POST.get("password")

        try:
            User.objects.get(username=username)
        except:
            messages.error(request, "User does not exist")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid credentials")

    return render(request, "base/authenticate.html", {"page_name": "login"})


def register_user(request):
    form = UserCreationForm()

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "An error occured during registration")

    return render(
        request, "base/authenticate.html", {"page_name": "register", "form": form}
    )


def logout_user(request):
    logout(request)
    return redirect("home")


def home(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) & Q(name__icontains=q) | Q(description__icontains=q)
    )
    topics = Topic.objects.all()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    return render(
        request,
        "base/home.html",
        {"rooms": rooms, "topics": topics, "room_messages": room_messages},
    )


def room(request, pk):
    room = Room.objects.get(id=pk)
    conversation = Message.objects.filter(room=pk)
    participants = room.participants.all()

    if request.method == "POST":
        Message.objects.create(
            user=request.user, room=room, body=request.POST.get("body")
        )
        room.participants.add(request.user)
        return redirect("room", pk=room.id)

    return render(
        request,
        "base/room.html",
        {"room": room, "conversation": conversation, "participants": participants},
    )


def user_profile(request, pk):
    user = User.objects.get(id=pk)
    rooms = Room.objects.filter(host=pk)
    room_messages = Message.objects.filter(user=pk)
    topics = Topic.objects.all()
    return render(
        request,
        "base/profile.html",
        {
            "user": user,
            "rooms": rooms,
            "room_messages": room_messages,
            "topics": topics,
        },
    )


@login_required(login_url="/auth")
def create_room(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == "POST":
        topic_name = request.POST.get("topic")
        topic, created = Topic.objects.get_or_create(name=topic_name)
        form = RoomForm(request.POST)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get("name"),
            description=request.POST.get("description"),
        )

        return redirect("home")

    return render(request, "base/room_form.html", {"form": form, "topics": topics})


@login_required(login_url="/auth")
def update_room(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    check_user_is_room_owner(request, room)

    if request.method == "POST":
        topic_name = request.POST.get("topic")
        topic, created = Topic.objects.get_or_create(name=topic_name)

        room.name = request.POST.get("name")
        room.description = request.POST.get("description")
        room.topic = topic
        room.save()

        return redirect("home")

    return render(
        request, "base/room_form.html", {"form": form, "topics": topics, "room": room}
    )


@login_required(login_url="/auth")
def delete_room(request, pk):
    room = Room.objects.get(id=pk)

    check_user_is_room_owner(request, room)

    if request.method == "POST":
        room.delete()
        return redirect("home")

    return render(request, "base/delete.html", {"obj": room})


@login_required(login_url="/auth")
def delete_message(request, pk):
    message = Message.objects.get(id=pk)

    check_user_is_message_sender(request, message)

    if request.method == "POST":
        message.delete()
        return redirect("home")

    return render(request, "base/delete.html", {"obj": message})
