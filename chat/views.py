
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login
from .models import ChatSession, ChatMessage, Attachement, AudioMessage
from .openrouter import ask_openrouter
from .utils import mime_dictionary, generate_tts_file
from django.core.files.base import ContentFile


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def login(request):
    pass

def logout(request):
    pass

@login_required
def home(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'chat/home.html', {'sessions': sessions})

@login_required
def session_create(request):
    if request.method == 'POST':
        name = request.POST.get('name') or 'New chat'
        session = ChatSession.objects.create(name=name, user=request.user)
        return redirect('session_detail', session_id=session.id)
    return render(request, 'chat/session_form.html')

@login_required
def session_detail(request, session_id):
    ALLOWED = ['text/plain', 'application/pdf', 'image/jpeg', 'image/png']
    MAX_SIZE = 5 * 1024 * 1024 #5mb
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    if request.method == 'POST':
        text = request.POST.get('message', '').strip()
        if not text and 'file' in request.FILES:
            return render(request, 'chat/session_detail.html',
                          {"session" : session,
                           "error" : "File or message should not be empty"})
        if text:
            file = request.FILES.get('file')
            ###WALIDACJA
            msg = ChatMessage.objects.create(session=session, role='user', content=text)
            
            if msg.contains(file):
                return render(request, 'chat/session_detail.html',
                          {"session" : session,
                           "error" : "No more than one file per message"})
            else:
                if file.size > MAX_SIZE:
                    return render(request, 'chat/session_detail.html',
                          {"session" : session,
                           "error" : "File is too large. Max size is 5mb"})
                if file.content_type not in ALLOWED:
                    (request, 'chat/session_detail.html',
                          {"session" : session,
                           "error" : "File type not supported"})
                Attachement.objects.create(message=msg, file=file, file_type=mime_dictionary.get(file.content_type), size=file.size)
            reply = ask_openrouter(msg)
            msg = ChatMessage.objects.create(session=session, role='assistant', content=reply)
            reply = ask_openrouter(msg)
            assistant_msg = ChatMessage.objects.create(session=session, role='assistant', content=reply)
            audio_bytes = generate_tts_file(reply)
            audio = AudioMessage.object.create()
            audio.file.save('reply.mp3', ContentFile(audio_bytes))
        return redirect('session_detail', session_id=session.id)
    return render(request, 'chat/session_detail.html', {'session': session})

