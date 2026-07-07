from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import Profile


def logout_view(request):
    logout(request)
    return redirect('/')


def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            try:
                profile = Profile.objects.get(user=user)

                if profile.role == "admin":
                    return redirect("admin_dashboard")

                elif profile.role == "guru":
                    return redirect("guru_dashboard")

                else:
                    return redirect("murid_dashboard")

            except Profile.DoesNotExist:
                return render(request, "accounts/login.html", {
                    "error": "Profile belum dibuat untuk user ini."
                })

        else:

            return render(request, "accounts/login.html", {
                "error": "Username atau Password salah"
            })

    return render(request, "accounts/login.html")