from django.urls import path
from . import views
# 2023 Haytham Jabbour hjabbour
app_name = 'SEreview'


urlpatterns = [
    path('', views.stats_view, name='stats'),
    path('forecasted-opportunity/', views.render_dynamic_form, {'form_name': 'forecasted_opportunity'}, name='forecasted_opportunity'),
    path('funnel-opportunity/', views.render_dynamic_form, {'form_name': 'funnel_opportunity'}, name='funnel_opportunity'),
    path('activity/', views.render_dynamic_form, {'form_name': 'activity'}, name='activity'),
    path('clients/', views.render_dynamic_form, {'form_name': 'clients'}, name='clients'),
    path('be-engagement-activity/', views.render_dynamic_form, {'form_name': 'be_engagement_activity'}, name='be_engagement_activity'),
    path('cx-engagement-activity/', views.render_dynamic_form, {'form_name': 'cx_engagement_activity'}, name='cx_engagement_activity'),
    path('tac-case/', views.render_dynamic_form, {'form_name': 'tac_case'}, name='tac_case'),
    path('issues/', views.render_dynamic_form, {'form_name': 'issues'}, name='issues'),
    path('meetings/', views.render_dynamic_form, {'form_name': 'meetings'}, name='meetings'),
    path('process-form/<str:form_name>/', views.process_form_view, name='process_form'),
    path('process-dash/<str:form_name>/', views.process_dash, name='process_dash'),
    path('process-dash-be/<str:form_name>/', views.process_dash_be, name='process_dash_be'),
    path('collections/<str:collection_name>/', views.collection_list, name='collection_list'),
    path('update/<str:collection_name>/<str:item_id>/', views.update_item, name='update_item'),
    path('delete_item/<str:collection_name>/<str:item_id>/', views.delete_item, name='delete_item'),
    path('stats/', views.stats_view, name='stats'),
    path('weeklyreview/', views.weeklyreview, name='weeklyreview'),
    path('mweeklyreview/<int:engineer_id>/', views.mweeklyreview, name='mweeklyreview'),
    path('mweeklyreview/', views.mweeklyreview, name='mweeklyreview'),
    path('engineerstats/', views.engineer_stats, name='engineerstats'),
    path('allstats/', views.all_stats, name='allstats'),
    path('monthlystats/', views.monthly_stats, name='monthlystats'),
    path('error/', views.error_page, name='error_page'),
    path('error/<str:message>/', views.error_page, name='error_page_with_message'),
    path('select_engineer/', views.select_engineer, name='select_engineer'),
    path('detail_item/<str:collection_name>/<str:item_id>/', views.detail_item, name='detail_item'),
    path('client-centric/', views.client_centric, name='client_centric'),
    path('client_dashboard/<str:client_id>/', views.client_dashboard, name='client_dashboard'),
    path('client_dashboard/<str:client_id>/<str:form_name>/', views.client_dashboard, name='client_dashboard_with_form'),
    path('client-centric_be/', views.client_centric_be, name='client_centric_be'),
    path('client-centric_be/<str:be_name>', views.client_centric_be, name='client_centric_be_name'),
    path('client_dashboard_be/<str:client_id>/', views.client_dashboard_be, name='client_dashboard_be'),
    path('client_dashboard_be/<str:client_id>/<str:form_name>/<str:be_name>/', views.client_dashboard_be, name='client_dashboard_be_with_form'),
    path('client_dashboard_be/<str:client_id>/<str:form_name>/<str:be_name>/<str:source>/', views.client_dashboard_be, name='client_dashboard_be_with_name'),
    path('process_dash_be/<str:form_name>/', views.process_dash_be, name='process_dash_be'),

]
