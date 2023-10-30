from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include

from paylio.frontend.sitemaps import StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap
}

urlpatterns = [
    path('boss/', admin.site.urls),
    path('', include('frontend.urls')),
    path('account/', include('account.urls', namespace='account')),
    path('account/transaction/',  include('transaction.urls', namespace='transaction')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemaps'),
]

admin.site.index_title = "Finease Bank Admin"
admin.site.site_header = "Finease Bank"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
