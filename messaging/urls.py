from django.urls import path
from . import views
from .views import send_webex_message

app_name = "messaging"  # This sets the namespace


urlpatterns = [
   path('send/', views.send_webex_message, name='send_message'),
   path('sendmwebex/', views.send_mwebex_message, name='send_mmessage'),
   path("add-webex-space/", views.add_webex_space, name="add_webex_space"),
   path("be-activity-report/", views.be_activity_report_view, name="be_activity_report")

]
