from rest_framework.routers import DefaultRouter
from .views import ExperimentViewSet, MobileAppViewSet, RankingCriteriaViewSet

router = DefaultRouter()
router.register(r'experiments', ExperimentViewSet, basename='experiment')
router.register(r'mobileapps', MobileAppViewSet, basename='mobileapp')
router.register(r'rankingcriteria', RankingCriteriaViewSet, basename='rankingcriteria')

urlpatterns = router.urls