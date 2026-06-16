from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from crm.api.frontend.restful.serializers.token_serializers import CustomTokenObtainPairView
from crm.api.frontend.restful.views.views import (
    DialogViewSet,
    dialog_messages,
    emulate_incoming,
    mark_dialog_read,
    teamlead_overview,
)

router = DefaultRouter()
router.register(r'dialogs', DialogViewSet, basename='dialog')

urlpatterns = [
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('', include(router.urls)),
    path('dialogs/<int:pk>/messages/', dialog_messages, name='dialog-messages'),
    path('dialogs/<int:pk>/read/', mark_dialog_read, name='dialog-read'),

    path('teamlead/overview/', teamlead_overview, name='teamlead-overview'),

    path('emulate/incoming/', emulate_incoming, name='emulate-incoming'),
]
