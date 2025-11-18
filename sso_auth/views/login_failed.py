from django.shortcuts import render


def login_failed(request):
    return render(
        request,
        "login_failed.html",
    )
