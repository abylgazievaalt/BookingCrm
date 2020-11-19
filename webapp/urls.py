
from django.urls import path, include

from webapp.views import IndexView, RoomListView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('list', RoomListView.as_view(), name='offers')
]
