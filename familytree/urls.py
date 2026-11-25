from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tree.urls')),
    # Fotos ausliefern – der Zugriff ist über Caddy/Authentik geschützt
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.AUTH_MODE == 'local':
    # Klassisches Login nur für die lokale Entwicklung
    urlpatterns = [
        path('login/', auth_views.LoginView.as_view(template_name='tree/login.html'), name='login'),
        path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    ] + urlpatterns
