"""
URL configuration for univesp_tcc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from seniorguard import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path("", views.home, name="home"),
    path("favicon.ico", RedirectView.as_view(url="/static/imagens/favicon.ico", permanent=True)),
    path("dashboard/<str:id>/", views.dashboard, name="dashboard"),
    path("update/", views.update, name="update"),
    path("device/<str:mac>/edit_name/", views.edit_device_name, name="edit_device_name"),
    path('device/<str:mac>/delete/', views.delete_device, name='delete_device'),
    path('device/<str:mac>/qrcode/', views.device_qrcode, name='device_qrcode'),
    path("api/sensor-history/<str:mac>/<str:sensor_type>/", views.sensor_history_api, name="sensor_history_api"),
]
