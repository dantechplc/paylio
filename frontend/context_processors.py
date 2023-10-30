from django.conf import settings

from frontend.models import CompanyProfile


def company(request):
    return {'company': CompanyProfile.objects.get(id=settings.COMPANY_ID)}
