
import os
import cv2
import numpy as np

from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.images import get_image_dimensions

from .models import ImageMatch


# ============================================================
# IMAGE PROCESSING HELPERS
# ============================================================

def load_image(image_path):
    """Load an image safely using OpenCV."""
    image = cv2.imread(image_path)

    if image is None:
        return None

    return image


def create_phash(image):
    """Create a simple perceptual hash."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (32, 32))
    resized = cv2.GaussianBlur(resized, (3, 3), 0)

    average = resized.mean()
    return resized > average


def phash_similarity(hash1, hash2):
    """Return perceptual hash similarity from 0 to 100."""
    difference = np.count_nonzero(hash1 != hash2)
    total = hash1.size

    similarity = 1 - (difference / total)
    return max(0.0, min(100.0, similarity * 100))


def color_similarity(image1, image2):
    """Compare HSV color histograms."""
    image1 = cv2.resize(image1, (256, 256))
    image2 = cv2.resize(image2, (256, 256))

    hsv1 = cv2.cvtColor(image1, cv2.COLOR_BGR2HSV)
    hsv2 = cv2.cvtColor(image2, cv2.COLOR_BGR2HSV)

    hist1 = cv2.calcHist(
        [hsv1], [0, 1], None, [50, 60],
        [0, 180, 0, 256]
    )
    hist2 = cv2.calcHist(
        [hsv2], [0, 1], None, [50, 60],
        [0, 180, 0, 256]
    )

    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)

    correlation = cv2.compareHist(
        hist1, hist2, cv2.HISTCMP_CORREL
    )

    similarity = ((correlation + 1) / 2) * 100
    return max(0.0, min(100.0, similarity))


def edge_similarity(image1, image2):
    """Compare the edge structure of two images."""
    image1 = cv2.resize(image1, (256, 256))
    image2 = cv2.resize(image2, (256, 256))

    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    edges1 = cv2.Canny(gray1, 50, 150)
    edges2 = cv2.Canny(gray2, 50, 150)

    edges1 = cv2.resize(edges1, (64, 64))
    edges2 = cv2.resize(edges2, (64, 64))

    difference = np.mean(
        np.abs(
            edges1.astype(float) -
            edges2.astype(float)
        )
    )

    similarity = 100 - (difference / 255 * 100)
    return max(0.0, min(100.0, similarity))


# ============================================================
# FIND BEST FRUIT MATCH
# ============================================================

def find_best_match(uploaded_path):
    """
    Compare an uploaded image against the fruit dataset.

    Score weights:
        50% perceptual hash
        30% color histogram
        20% edge similarity

    Dataset structure:
        dataset/apple/
        dataset/banana/
        dataset/mango/
        dataset/orange/
        dataset/strawberry/
    """

    uploaded_image = load_image(uploaded_path)

    if uploaded_image is None:
        return None

    uploaded_hash = create_phash(uploaded_image)

    dataset_path = os.path.join(
        settings.BASE_DIR, "dataset"
    )

    fruit_folders = [
        "apple",
        "banana",
        "mango",
        "orange",
        "strawberry",
    ]

    best_match = None

    for fruit in fruit_folders:
        fruit_path = os.path.join(dataset_path, fruit)

        if not os.path.isdir(fruit_path):
            continue

        for filename in os.listdir(fruit_path):
            if not filename.lower().endswith(
                (".jpg", ".jpeg", ".png", ".webp")
            ):
                continue

            dataset_image_path = os.path.join(
                fruit_path, filename
            )

            dataset_image = load_image(dataset_image_path)

            if dataset_image is None:
                continue

            dataset_hash = create_phash(dataset_image)

            phash_score = phash_similarity(
                uploaded_hash, dataset_hash
            )

            color_score = color_similarity(
                uploaded_image, dataset_image
            )

            edge_score = edge_similarity(
                uploaded_image, dataset_image
            )

            final_score = (
                phash_score * 0.50
                + color_score * 0.30
                + edge_score * 0.20
            )

            if (
                best_match is None
                or final_score > best_match["similarity"]
            ):
                best_match = {
                    "fruit": fruit.capitalize(),
                    "similarity": round(final_score, 2),
                    "image_path": dataset_image_path,
                    "filename": filename,
                }

    return best_match


# ============================================================
# HOME PAGE
# ============================================================

def home(request):
    return render(request, "prediction/home.html")


# ============================================================
# UPLOAD AND MATCH IMAGE
# ============================================================

def upload_image(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get("uploaded_image")

        if not uploaded_file:
            return render(
                request,
                "prediction/upload.html",
                {"error": "Please select an image to upload."},
            )

        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        extension = os.path.splitext(uploaded_file.name)[1].lower()

        if extension not in allowed_extensions:
            return render(
                request,
                "prediction/upload.html",
                {
                    "error": (
                        "Unsupported file format. "
                        "Please upload a JPG, JPEG, PNG, or WEBP image."
                    )
                },
            )

        # Save the uploaded image.
        image_match = ImageMatch.objects.create(
            uploaded_image=uploaded_file
        )

        try:
            # Compare against the reference dataset.
            best_match = find_best_match(
                image_match.uploaded_image.path
            )

            if best_match:
                image_match.matched_fruit = best_match["fruit"]
                image_match.similarity_score = best_match["similarity"]
            else:
                image_match.matched_fruit = "Unknown"
                image_match.similarity_score = 0.0

            image_match.save()

        except Exception:
            # Remove the failed record and its uploaded file.
            image_path = image_match.uploaded_image.path

            image_match.delete()

            if os.path.exists(image_path):
                os.remove(image_path)

            return render(
                request,
                "prediction/upload.html",
                {
                    "error": (
                        "The image could not be processed. "
                        "Check that your dataset folders contain valid images."
                    )
                },
            )

        return redirect(
            "upload_success",
            pk=image_match.pk
        )

    return render(request, "prediction/upload.html")


# ============================================================
# RESULT PAGE
# ============================================================

def upload_success(request, pk):
    image_match = get_object_or_404(ImageMatch, pk=pk)

    return render(
        request,
        "prediction/upload_success.html",
        {"image_match": image_match},
    )


# ============================================================
# IMAGE MATCH HISTORY
# ============================================================

def history(request):
    matches = ImageMatch.objects.all().order_by("-created_at")

    return render(
        request,
        "prediction/history.html",
        {
            "matches": matches,
            "history": matches,
        },
    )


# ============================================================
# LOGIN PAGE
# ============================================================

def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")

    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            auth_login(request, user)
            return redirect("home")

        error = "Invalid username or password. Please try again."

    return render(
        request,
        "prediction/login.html",
        {"error": error},
    )