import os
import cv2
import numpy as np

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import ImageMatch


# ============================================================
# IMAGE PROCESSING HELPERS
# ============================================================

def load_image(image_path):
    """
    Load an image safely using OpenCV.
    """

    image = cv2.imread(image_path)

    if image is None:
        return None

    return image


def create_phash(image):
    """
    Create a simple perceptual hash.
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    resized = cv2.resize(
        gray,
        (32, 32)
    )

    resized = cv2.GaussianBlur(
        resized,
        (3, 3),
        0
    )

    average = resized.mean()

    return resized > average


def phash_similarity(hash1, hash2):
    """
    Return perceptual hash similarity from 0 to 100.
    """

    difference = np.count_nonzero(
        hash1 != hash2
    )

    total = hash1.size

    similarity = 1 - (
        difference / total
    )

    return max(
        0.0,
        min(
            100.0,
            similarity * 100
        )
    )


def color_similarity(image1, image2):
    """
    Compare HSV color histograms.
    """

    image1 = cv2.resize(
        image1,
        (256, 256)
    )

    image2 = cv2.resize(
        image2,
        (256, 256)
    )

    hsv1 = cv2.cvtColor(
        image1,
        cv2.COLOR_BGR2HSV
    )

    hsv2 = cv2.cvtColor(
        image2,
        cv2.COLOR_BGR2HSV
    )

    hist1 = cv2.calcHist(
        [hsv1],
        [0, 1],
        None,
        [50, 60],
        [0, 180, 0, 256]
    )

    hist2 = cv2.calcHist(
        [hsv2],
        [0, 1],
        None,
        [50, 60],
        [0, 180, 0, 256]
    )

    cv2.normalize(
        hist1,
        hist1
    )

    cv2.normalize(
        hist2,
        hist2
    )

    correlation = cv2.compareHist(
        hist1,
        hist2,
        cv2.HISTCMP_CORREL
    )

    similarity = (
        (correlation + 1) / 2
    ) * 100

    return max(
        0.0,
        min(
            100.0,
            similarity
        )
    )


def edge_similarity(image1, image2):
    """
    Compare edge structure of two images.
    """

    image1 = cv2.resize(
        image1,
        (256, 256)
    )

    image2 = cv2.resize(
        image2,
        (256, 256)
    )

    gray1 = cv2.cvtColor(
        image1,
        cv2.COLOR_BGR2GRAY
    )

    gray2 = cv2.cvtColor(
        image2,
        cv2.COLOR_BGR2GRAY
    )

    edges1 = cv2.Canny(
        gray1,
        50,
        150
    )

    edges2 = cv2.Canny(
        gray2,
        50,
        150
    )

    edges1 = cv2.resize(
        edges1,
        (64, 64)
    )

    edges2 = cv2.resize(
        edges2,
        (64, 64)
    )

    difference = np.mean(
        np.abs(
            edges1.astype(float)
            -
            edges2.astype(float)
        )
    )

    similarity = (
        100 -
        (
            difference / 255 * 100
        )
    )

    return max(
        0.0,
        min(
            100.0,
            similarity
        )
    )


# ============================================================
# FIND BEST FRUIT MATCH
# ============================================================

def find_best_match(uploaded_path):
    """
    Compare uploaded image against the fruit dataset.

    Matching algorithm:

        50% perceptual hash
        30% color histogram
        20% edge similarity

    Dataset structure:

        dataset/
            apple/
            banana/
            mango/
            orange/
            strawberry/
    """

    uploaded_image = load_image(
        uploaded_path
    )

    if uploaded_image is None:
        return None

    uploaded_hash = create_phash(
        uploaded_image
    )

    dataset_path = os.path.join(
        settings.BASE_DIR,
        "dataset"
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

        fruit_path = os.path.join(
            dataset_path,
            fruit
        )

        # Skip folder if it does not exist
        if not os.path.isdir(
            fruit_path
        ):
            continue

        try:
            filenames = os.listdir(
                fruit_path
            )
        except OSError:
            continue

        for filename in filenames:

            if not filename.lower().endswith(
                (
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp"
                )
            ):
                continue

            dataset_image_path = os.path.join(
                fruit_path,
                filename
            )

            dataset_image = load_image(
                dataset_image_path
            )

            if dataset_image is None:
                continue

            try:

                # --------------------------------------------
                # PERCEPTUAL HASH
                # --------------------------------------------

                dataset_hash = create_phash(
                    dataset_image
                )

                phash_score = phash_similarity(
                    uploaded_hash,
                    dataset_hash
                )

                # --------------------------------------------
                # COLOR
                # --------------------------------------------

                color_score = color_similarity(
                    uploaded_image,
                    dataset_image
                )

                # --------------------------------------------
                # EDGES
                # --------------------------------------------

                edge_score = edge_similarity(
                    uploaded_image,
                    dataset_image
                )

                # --------------------------------------------
                # FINAL SCORE
                # --------------------------------------------

                final_score = (
                    phash_score * 0.50
                    +
                    color_score * 0.30
                    +
                    edge_score * 0.20
                )

                final_score = max(
                    0.0,
                    min(
                        100.0,
                        final_score
                    )
                )

                # --------------------------------------------
                # BEST MATCH
                # --------------------------------------------

                if (
                    best_match is None
                    or final_score
                    > best_match["similarity"]
                ):

                    best_match = {
                        "fruit": fruit.capitalize(),
                        "similarity": round(
                            final_score,
                            2
                        ),
                        "image_path": dataset_image_path,
                        "filename": filename,
                    }

            except Exception as e:

                print(
                    f"Error processing {dataset_image_path}:",
                    e
                )

                continue

    return best_match


# ============================================================
# HOME PAGE
# ============================================================

def home(request):
    """
    Public home page.
    """

    return render(
        request,
        "prediction/home.html"
    )


# ============================================================
# UPLOAD AND MATCH IMAGE
# ============================================================

@login_required(login_url="/login/")
def upload_image(request):
    """
    Upload an image and compare it with the fruit dataset.
    """

    if request.method == "POST":

        uploaded_file = request.FILES.get(
            "uploaded_image"
        )

        # ----------------------------------------------------
        # CHECK IMAGE
        # ----------------------------------------------------

        if not uploaded_file:

            return render(
                request,
                "prediction/upload.html",
                {
                    "error": (
                        "Please select an image "
                        "to upload."
                    )
                }
            )

        # ----------------------------------------------------
        # CHECK FILE EXTENSION
        # ----------------------------------------------------

        allowed_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        }

        extension = os.path.splitext(
            uploaded_file.name
        )[1].lower()

        if extension not in allowed_extensions:

            return render(
                request,
                "prediction/upload.html",
                {
                    "error": (
                        "Unsupported file format. "
                        "Please upload JPG, JPEG, PNG, "
                        "or WEBP image."
                    )
                }
            )

        # ----------------------------------------------------
        # CHECK FILE SIZE
        # ----------------------------------------------------

        max_file_size = 10 * 1024 * 1024

        if uploaded_file.size > max_file_size:

            return render(
                request,
                "prediction/upload.html",
                {
                    "error": (
                        "Image size is too large. "
                        "Please upload an image below 10 MB."
                    )
                }
            )

        # ----------------------------------------------------
        # SAVE IMAGE
        #
        # IMPORTANT:
        # Save the logged-in user with the record.
        # This is required for private user history.
        # ----------------------------------------------------

        image_match = ImageMatch.objects.create(
            user=request.user,
            uploaded_image=uploaded_file
        )

        try:

            # ------------------------------------------------
            # FIND BEST MATCH
            # ------------------------------------------------

            best_match = find_best_match(
                image_match.uploaded_image.path
            )

            if best_match:

                image_match.matched_fruit = (
                    best_match["fruit"]
                )

                image_match.similarity_score = (
                    best_match["similarity"]
                )

            else:

                image_match.matched_fruit = "Unknown"

                image_match.similarity_score = 0.0

            # ------------------------------------------------
            # SAVE RESULT
            # ------------------------------------------------

            image_match.save()

        except Exception as e:

            print(
                "Image processing error:",
                e
            )

            try:

                image_path = (
                    image_match.uploaded_image.path
                )

            except Exception:

                image_path = None

            image_match.delete()

            if (
                image_path
                and os.path.exists(image_path)
            ):

                try:
                    os.remove(image_path)
                except OSError:
                    pass

            return render(
                request,
                "prediction/upload.html",
                {
                    "error": (
                        "The image could not be processed. "
                        "Please check that your dataset folders "
                        "contain valid images."
                    )
                }
            )

        # ----------------------------------------------------
        # GO TO RESULT PAGE
        # ----------------------------------------------------

        return redirect(
            "upload_success",
            pk=image_match.pk
        )

    # --------------------------------------------------------
    # GET REQUEST
    # --------------------------------------------------------

    return render(
        request,
        "prediction/upload.html"
    )


# ============================================================
# RESULT PAGE
# ============================================================

@login_required(login_url="/login/")
def upload_success(request, pk):
    """
    Display the matching result.

    Normal users can only view their own result.

    Admin/staff users can view any result.
    """

    # --------------------------------------------------------
    # ADMIN / STAFF
    # --------------------------------------------------------

    if (
        request.user.is_staff
        or request.user.is_superuser
    ):

        image_match = get_object_or_404(
            ImageMatch,
            pk=pk
        )

    # --------------------------------------------------------
    # NORMAL USER
    # --------------------------------------------------------

    else:

        image_match = get_object_or_404(
            ImageMatch,
            pk=pk,
            user=request.user
        )

    return render(
        request,
        "prediction/upload_success.html",
        {
            "image_match": image_match
        }
    )


# ============================================================
# IMAGE MATCH HISTORY
# ============================================================

@login_required(login_url="/login/")
def history(request):
    """
    Display image matching history.

    Normal user:
        Only their own history.

    Admin/staff:
        All users' history.
    """

    # --------------------------------------------------------
    # ADMIN / STAFF
    # --------------------------------------------------------

    if (
        request.user.is_staff
        or request.user.is_superuser
    ):

        matches = ImageMatch.objects.all().order_by(
            "-created_at"
        )

    # --------------------------------------------------------
    # NORMAL USER
    # --------------------------------------------------------

    else:

        matches = ImageMatch.objects.filter(
            user=request.user
        ).order_by(
            "-created_at"
        )

    return render(
        request,
        "prediction/history.html",
        {
            "matches": matches,
            "history": matches,
        }
    )