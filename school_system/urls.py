"""
URL configuration for school_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# school_system/urls.py

from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
# 添加 Bearer Token 驗證
swagger_info = openapi.Info(
    title="API Documentation",
    default_version="v1",
    description="API endpoints requiring Bearer Token.",
    terms_of_service="https://www.google.com/policies/terms/",
)

# swagger_settings = {
#     'SECURITY_DEFINITIONS': {
#         'Bearer': {
#             'type': 'apiKey',
#             'name': 'Authorization',
#             'in': 'header',
#         },
#     },
# }


schema_view = get_schema_view(
    openapi.Info(
        title="School System API",
        default_version='v1',
        description="API documentation for School System Project",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@school.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
schema_view.with_ui('swagger', cache_timeout=0)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('user.urls')),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]