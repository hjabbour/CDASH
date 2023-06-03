from django.urls import path
from . import views

app_name = 'SEreview'


urlpatterns = [
    path('forecasted-opportunity/', views.forecasted_opportunity_view, name='forecasted_opportunity'),
    path('funnel-opportunity/', views.funnel_opportunity_view, name='funnel_opportunity'),
    path('be-engagement-activity/', views.be_engagement_activity_view, name='be_engagement_activity'),
    path('cx-engagement-activity/', views.cx_engagement_activity_view, name='cx_engagement_activity'),
    path('tac-case/', views.tac_case_view, name='tac_case'),
    path('process-form/<str:form_name>/', views.process_form_view, name='process_form'),
]