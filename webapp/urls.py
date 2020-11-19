
from django.urls import path, include

from webapp.views import IndexView

urlpatterns = [
    path('', IndexView.as_view()),
]
