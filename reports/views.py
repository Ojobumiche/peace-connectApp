from django.shortcuts import render
from .services import community_summary

# Create your views here.

def dashboard(request):

    summary = community_summary()

    return render(
        request,
        "reports/dashboard.html",
        {
            "summary": summary
        }
    )



