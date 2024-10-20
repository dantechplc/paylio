from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    protocol = 'https'
    def items(self):
        return ['about', 'freelancer', 'home', 'help_center', 'terms', 'security', 'account:register', 'account:login']

    def location(self, item):
        return reverse(item)
