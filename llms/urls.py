from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConfigurationViewSet, LLMViewSet, ConfiguredModelViewSet

router = DefaultRouter()
router.register(r'llms', LLMViewSet)
router.register(r'configurations', ConfigurationViewSet)
router.register(r'configured-models', ConfiguredModelViewSet)

urlpatterns = [
    path('', include(router.urls)),
]