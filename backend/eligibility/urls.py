from rest_framework.routers import DefaultRouter

from .views import EligibilityCheckViewSet

router = DefaultRouter()
router.register("", EligibilityCheckViewSet, basename="eligibility")

urlpatterns = router.urls
