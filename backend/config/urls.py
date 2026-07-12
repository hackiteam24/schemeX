"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/chat/", include("chatbots.urls")),
    path("api/profile/", include("profiles.urls")),
    path("api/schemes/", include("schemes.urls")),
    path("api/eligibility/", include("eligibility.urls")),
    path("api/applications/", include("applications.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    # Frontend routes
    path("", TemplateView.as_view(template_name="home/index.html"), name="home"),
    path(
        "about/", TemplateView.as_view(template_name="about/index.html"), name="about"
    ),
    path(
        "contact/",
        TemplateView.as_view(template_name="about/index.html"),
        name="contact",
    ),
    path("login/", TemplateView.as_view(template_name="auth/login.html"), name="login"),
    path(
        "register/",
        TemplateView.as_view(template_name="auth/register.html"),
        name="register",
    ),
    path(
        "dashboard/",
        TemplateView.as_view(template_name="dashboard/index.html"),
        name="dashboard",
    ),
    path(
        "admin-dashboard/",
        TemplateView.as_view(template_name="dashboard/admin.html"),
        name="admin_dashboard",
    ),
    path(
        "profile/",
        TemplateView.as_view(template_name="profile/index.html"),
        name="profile",
    ),
    path(
        "schemes/",
        TemplateView.as_view(template_name="schemes/index.html"),
        name="schemes",
    ),
    path(
        "schemes/<uuid:pk>/",
        TemplateView.as_view(template_name="schemes/detail.html"),
        name="scheme_detail",
    ),
    path(
        "eligibility/",
        TemplateView.as_view(template_name="eligibility/index.html"),
        name="eligibility",
    ),
    path(
        "application/",
        TemplateView.as_view(template_name="application/index.html"),
        name="application_form",
    ),
    path(
        "documents/",
        TemplateView.as_view(template_name="documents/index.html"),
        name="documents",
    ),
    path(
        "chat/", TemplateView.as_view(template_name="chat/index.html"), name="chatbot"
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
