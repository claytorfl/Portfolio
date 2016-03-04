from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from django.contrib import admin

#URL's for the main website, admin page, and change password
urlpatterns = [

    #Imports urls from chem folder for the chemistry website
    url(r'^chem/', include('chem.urls', namespace="chem")),

    #Adds urls for admin site
    url(r'^admin/', include(admin.site.urls)),

    #Adds url for Django default Reset Password View
    url('^', include('django.contrib.auth.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
