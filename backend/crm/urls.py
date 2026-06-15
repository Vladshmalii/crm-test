from django.urls import path, include

urlpatterns = [
    path('', include('crm.api.urls')),
]
