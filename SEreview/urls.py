from django.urls import path
from . import views
# 2023 Haytham Jabbour hjabbour
app_name = 'SEreview'

urlpatterns = [
    path('', views.stats_view, name='stats'),
    path('forecasted-opportunity/', views.forecasted_opportunity_view, name='forecasted_opportunity'),
    path('funnel-opportunity/', views.funnel_opportunity_view, name='funnel_opportunity'),
    path('activity/', views.activity_view, name='activity'),
    path('be-engagement-activity/', views.be_engagement_activity_view, name='be_engagement_activity'),
    path('cx-engagement-activity/', views.cx_engagement_activity_view, name='cx_engagement_activity'),
    path('tac-case/', views.tac_case_view, name='tac_case'),
    path('issues/', views.issues_view, name='issues'),
    path('meetings/', views.meetings_view, name='meetings'),
    path('process-form/<str:form_name>/', views.process_form_view, name='process_form'),
    path('collections/<str:collection_name>/', views.collection_list, name='collection_list'),
    path('update/<str:collection_name>/<str:item_id>/', views.update_item, name='update_item'),
    path('delete_item/<str:collection_name>/<str:item_id>/', views.delete_item, name='delete_item'),
    path('stats/', views.stats_view, name='stats'),
    path('weeklyreview/', views.weeklyreview, name='weeklyreview'),
    path('mweeklyreview/<int:engineer_id>/', views.mweeklyreview, name='mweeklyreview'),
    path('error/', views.error_page, name='error_page'),
    path('select_engineer/', views.select_engineer, name='select_engineer'),

]