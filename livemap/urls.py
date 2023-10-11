from django.urls import path

from livemap.views import index

urlpatterns = [
    path("", index, name="index"),
]

app_name = "livemap"
