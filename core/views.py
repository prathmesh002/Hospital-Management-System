from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import ContactForm
from .models import SitePage


def index(request):
    """Public landing page + contact form (PHP: index.php)."""
    if request.method == "POST":
        form = ContactForm({
            "full_name": request.POST.get("fullname", ""),
            "email": request.POST.get("emailid", ""),
            "contact_no": request.POST.get("mobileno", ""),
            "message": request.POST.get("description", ""),
        })
        if form.is_valid():
            form.save()
            messages.success(request, "Your information was successfully submitted.")
        else:
            messages.error(request, "Please check your details (a valid e-mail address is required).")
        return redirect("/#contact_us")
    return render(request, "core/index.html", {
        "about": SitePage.objects.filter(page_type=SitePage.ABOUT).first(),
        "contact": SitePage.objects.filter(page_type=SitePage.CONTACT).first(),
    })
