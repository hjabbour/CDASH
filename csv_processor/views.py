
# Create your views here.
from django.shortcuts import render, redirect
from pymongo import MongoClient
import pandas as pd
from .forms import UploadCSVForm
#from .forms import UploadCSVForm
from .models import UploadedFile
from django.conf import settings
from django.http import HttpResponse


import os


def delete_files(request):
    if request.method == 'POST':
        selected_files = request.POST.getlist('selected_files')
        if selected_files:
            # Delete files from the file system
            folder_path = os.path.join(settings.MEDIA_ROOT, 'csv_files')
            for file_name in selected_files:
                file_path = os.path.join(folder_path, file_name)
                if os.path.exists(file_path):
                    os.remove(file_path)

            # Delete records from the database
            UploadedFile.objects.filter(csv_file__in=selected_files).delete()
            
        return redirect('csv_processor:file_list')
    return render(request, 'csv_processor/file_list.html')



def upload_csv(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']

            # Save the uploaded file
            uploaded_file = UploadedFile(csv_file=csv_file)
            uploaded_file.save()

            # Redirect to the file list view on successful upload
            return redirect('csv_processor:file_list')
    else:
        form = UploadCSVForm()

    context = {
        'form': form
    }
    return render(request, 'csv_processor/upload_csv.html', context)


def file_list(request):
    # Get the list of files in the csv_files folder
    folder_path = os.path.join(settings.MEDIA_ROOT, 'csv_files')
    files = os.listdir(folder_path)
    
    context = {
        'files': files
    }
    return render(request, 'csv_processor/file_list.html', context)

def file_detail(request, filename):
    # Open and read the selected file
    file_path = os.path.join(settings.MEDIA_ROOT, 'csv_files', filename)
    with open(file_path, 'r') as file:
        content = file.read()
    
    context = {
        'filename': filename,
        'content': content
    }
    return render(request, 'csv_processor/file_detail.html', context)



def file_columns(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, 'csv_files', filename)
    # Code to read the CSV file and extract the column names
    # You can use the csv module or pandas to read the file and extract the columns
    
    # Example using pandas:
    import pandas as pd
    df = pd.read_csv(file_path)
    columns = df.columns.tolist()
    
    context = {
        'filename': filename,
        'selected_file': filename,
        'columns': columns,
    
    }
    return render(request, 'csv_processor/file_columns.html', context)


def process_columns(request,filename):
    if request.method == 'POST':
        
        # Retrieve selected columns from the form data
        selected_columns = request.POST.getlist('columns')
        selected_file = request.POST.get('filename')
        file_path = os.path.join(settings.MEDIA_ROOT, 'csv_files', filename)
        df = pd.read_csv(file_path)
        new_df=df[selected_columns]
        
        context = {
        'filename': filename,
        'selected_file': filename,
        'columns': selected_columns,
        'df':new_df,
    
    }
        
    return render(request, 'csv_processor/new_columns.html', context)

        # Process the selected columns
        # ...

        # Return an appropriate response, such as a redirect or a success message


    # Process the selected columns as needed (insert into MongoDB or return as pandas dataframe)
    #
