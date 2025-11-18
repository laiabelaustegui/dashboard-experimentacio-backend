from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LLMViewSet

router = DefaultRouter()
router.register(r'llms', LLMViewSet)

urlpatterns = [
    path('', include(router.urls)),
]