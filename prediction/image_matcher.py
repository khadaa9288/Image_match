import os

import cv2
import numpy as np

from django.conf import settings


# ============================================================
# IMAGE MATCHING CONFIGURATION
# ============================================================

SUPPORTED_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
)


# ============================================================
# LOAD IMAGE
# ============================================================

def load_image(image_path):
    """
    Load an image using OpenCV.
    """

    image = cv2.imread(image_path)

    if image is None:
        return None

    return image


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(image):
    """
    Resize image and convert it into HSV format.

    HSV is useful for comparing fruit colors.
    """

    image = cv2.resize(
        image,
        (224, 224)
    )

    hsv_image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV
    )

    return hsv_image


# ============================================================
# COLOR HISTOGRAM
# ============================================================

def calculate_histogram(image):
    """
    Calculate normalized HSV histogram.
    """

    hsv_image = preprocess_image(image)

    histogram = cv2.calcHist(
        [hsv_image],
        [0, 1],
        None,
        [50, 60],
        [0, 180, 0, 256]
    )

    cv2.normalize(
        histogram,
        histogram
    )

    return histogram


# ============================================================
# IMAGE SIMILARITY
# ============================================================

def calculate_similarity(image1, image2):
    """
    Calculate similarity between two images.

    Returns a percentage from 0 to 100.
    """

    histogram1 = calculate_histogram(image1)
    histogram2 = calculate_histogram(image2)

    similarity = cv2.compareHist(
        histogram1,
        histogram2,
        cv2.HISTCMP_CORREL
    )

    # Convert correlation range to 0-100.
    similarity = ((similarity + 1) / 2) * 100

    similarity = max(
        0,
        min(100, similarity)
    )

    return round(similarity, 2)


# ============================================================
# GET DATASET IMAGES
# ============================================================

def get_dataset_images():
    """
    Get all fruit images from the dataset directory.
    """

    dataset_path = os.path.join(
        settings.BASE_DIR,
        "dataset"
    )

    dataset_images = []

    if not os.path.exists(dataset_path):
        return dataset_images

    for fruit_name in os.listdir(dataset_path):

        fruit_folder = os.path.join(
            dataset_path,
            fruit_name
        )

        if not os.path.isdir(fruit_folder):
            continue

        for filename in os.listdir(fruit_folder):

            if not filename.lower().endswith(
                SUPPORTED_EXTENSIONS
            ):
                continue

            image_path = os.path.join(
                fruit_folder,
                filename
            )

            dataset_images.append({
                "fruit": fruit_name.capitalize(),
                "path": image_path,
                "filename": filename,
            })

    return dataset_images


# ============================================================
# FIND BEST MATCH
# ============================================================

def find_best_match(uploaded_image_path):
    """
    Compare uploaded image with all dataset images.

    Returns the best matching fruit and similarity.
    """

    uploaded_image = load_image(
        uploaded_image_path
    )

    if uploaded_image is None:
        return None

    dataset_images = get_dataset_images()

    if not dataset_images:
        return None

    best_match = None
    best_similarity = -1

    for dataset_item in dataset_images:

        known_image = load_image(
            dataset_item["path"]
        )

        if known_image is None:
            continue

        similarity = calculate_similarity(
            uploaded_image,
            known_image
        )

        if similarity > best_similarity:

            best_similarity = similarity

            best_match = {
                "fruit": dataset_item["fruit"],
                "similarity": similarity,
                "image": dataset_item["path"],
                "filename": dataset_item["filename"],
            }

    return best_match