from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView, ListView

from webapp.models import Guestroom


class IndexView(TemplateView):
    template_name = 'index.html'


class RoomListView(ListView):
    model = Guestroom
    template_name = 'offers.html'
