from django.shortcuts import render


def logout_success(request):
    return render(request, "logout_success.html")
