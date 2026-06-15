from django.urls import path, include

urlpatterns = [
    path('api/', include('crm.api.urls')),
]
