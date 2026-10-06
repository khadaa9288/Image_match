from django.urls import path

from . import views


urlpatterns = [

    # ============================================================
    # HOME
    # ============================================================
    path(
        "",
        views.home,
        name="home"
    ),

    # ============================================================
    # IMAGE MATCHING
    # ============================================================
    path(
        "upload/",
        views.upload_image,
        name="upload_image"
    ),

    # ============================================================
    # MATCHING RESULT
    # ============================================================
    path(
        "success/<int:pk>/",
        views.upload_success,
        name="upload_success"
    ),

    # ============================================================
    # USER MATCHING HISTORY
    # ============================================================
    path(
        "history/",
        views.history,
        name="history"
    ),
]