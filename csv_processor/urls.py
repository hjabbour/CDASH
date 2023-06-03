from django.urls import path
from . import views

app_name = 'csv_processor'

urlpatterns = [
    path('upload-csv/', views.upload_csv, name='upload_csv'),
    path('files/', views.file_list, name='file_list'),
    path('files/<str:filename>/', views.file_detail, name='file_detail'),
    path('files/edit/<str:filename>/', views.file_columns, name='file_columns'),
    path('process_columns/<str:filename>/', views.process_columns, name='process_columns'),
    path('delete_files/', views.delete_files, name='delete_files'),
    path('process_ppt/', views.process_ppt, name='process_ppt'),
    path('insert_into_mongodb/', views.insert_into_mongodb, name='insert_into_mongodb'),
    
]