from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConfigurationViewSet, LLMViewSet

router = DefaultRouter()
router.register(r'llms', LLMViewSet)
router.register(r'configurations', ConfigurationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]