from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "school_menu"

urlpatterns = [
    path("", views.index, name="index"),
    path("settings/<int:pk>/", views.settings_view, name="settings"),
    path("school_list", views.school_list, name="school_list"),
    path(
        "get-menu/<int:week>/<int:day>/<int:type>/<int:school_id>/",
        views.get_menu,
        name="get_menu",
    ),
    path("info", TemplateView.as_view(template_name="pages/info.html"), name="info"),
    # TODO: get this url back when ISSUE #34 is implemented
    # path("json_menu", views.json_menu, name="json_menu"),
    path("menu/<slug:slug>/", views.school_menu, name="school_menu"),
    path(
        "menu/<int:school_id>/<int:week>/<int:season>/",
        views.create_weekly_menu,
        name="create_weekly_menu",
    ),
]

htmx_urlpatterns = [
    path("school/", views.school_view, name="school_view"),
    path("school/create/", views.school_create, name="school_create"),
    path("school/update/", views.school_update, name="school_update"),
    path("menu/<int:school_id>/upload/", views.upload_menu, name="upload_menu"),
    path("settings/<int:pk>/menu/", views.menu_settings_partial, name="menu_settings"),
    path("search-schools/", views.search_schools, name="search_schools"),
]

urlpatterns += htmx_urlpatterns
