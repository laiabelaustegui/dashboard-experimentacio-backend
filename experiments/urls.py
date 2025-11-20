from django.urls import path
from .views import CustomExperimentCreate

urlpatterns = [
    path('', CustomExperimentCreate.as_view(), name='create-experiment'),
]
