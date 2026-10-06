from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect


# ============================================================
# USER LOGIN
# ============================================================

def user_login(request):

    if request.user.is_authenticated:

        if request.user.is_staff:
            return redirect("/admin/")

        return redirect("home")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            # Admin must use Admin Login
            if user.is_staff:

                messages.warning(
                    request,
                    "This is an admin account. "
                    "Please use Admin Login."
                )

                return redirect(
                    "admin_login"
                )

            login(
                request,
                user
            )

            messages.success(
                request,
                f"Welcome back, {user.username}!"
            )

            return redirect("home")

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "prediction/login.html"
    )


# ============================================================
# REGISTER
# ============================================================

def register(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        if not username:

            messages.error(
                request,
                "Please enter a username."
            )

            return render(
                request,
                "prediction/register.html"
            )

        if not password:

            messages.error(
                request,
                "Please enter a password."
            )

            return render(
                request,
                "prediction/register.html"
            )

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return render(
                request,
                "prediction/register.html"
            )

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return render(
                request,
                "prediction/register.html"
            )

        User.objects.create_user(
            username=username,
            password=password
        )

        messages.success(
            request,
            "Registration successful. "
            "Please login."
        )

        return redirect("login")

    return render(
        request,
        "prediction/register.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@login_required(login_url="/login/")
def user_logout(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("home")


# ============================================================
# ADMIN LOGIN
# ============================================================

def admin_login(request):

    if request.user.is_authenticated:

        if request.user.is_staff:
            return redirect("/admin/")

        return redirect("home")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if user.is_staff:

                login(
                    request,
                    user
                )

                messages.success(
                    request,
                    f"Welcome Admin, {user.username}!"
                )

                return redirect("/admin/")

        messages.error(
            request,
            "Invalid admin credentials."
        )

    return render(
        request,
        "prediction/admin_login.html"
    )