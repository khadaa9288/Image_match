from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from accounts import views as account_views


urlpatterns = [

    # Django Admin
    path(
        "admin/",
        admin.site.urls
    ),

    # Prediction / Image Match
    path(
        "",
        include("prediction.urls")
    ),

    # User Login
    path(
        "login/",
        account_views.user_login,
        name="login"
    ),

    # Register
    path(
        "register/",
        account_views.register,
        name="register"
    ),

    # Logout
    path(
        "logout/",
        account_views.user_logout,
        name="logout"
    ),

    # Admin Login
    path(
        "admin-login/",
        account_views.admin_login,
        name="admin_login"
    ),
]


if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )