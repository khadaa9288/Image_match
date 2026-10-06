from django.db import models
from django.contrib.auth.models import User


class ImageMatch(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="image_matches",
        null=True,
        blank=True
    )

    uploaded_image = models.ImageField(
        upload_to="image_match/"
    )

    matched_fruit = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    similarity_score = models.FloatField(
        default=0.0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.matched_fruit} - {self.similarity_score}%"