from django.contrib import admin
from .models import ImageMatch


@admin.register(ImageMatch)
class ImageMatchAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "uploaded_image",
        "matched_fruit",
        "similarity_score",
        "created_at",
    )

    list_filter = (
        "matched_fruit",
        "created_at",
    )

    search_fields = (
        "matched_fruit",
    )

    readonly_fields = (
        "created_at",
    )