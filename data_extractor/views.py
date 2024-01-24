# Import magic for .zip file validator
import magic

import re
import shutil
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.core.files.storage import FileSystemStorage
import os
import zipfile
import easyocr

#new
from django.contrib import messages


def extract_folder(request):
    #print(request.session.items())
    request.session.save()
    session_id = request.session.session_key
    #session_id = request.session.keys()
    print(session_id)
    if request.method == 'POST':
        
        uploaded_file = request.FILES['zipfile']

         # Validate the uploaded file using magic library
        mime_type = magic.from_buffer(uploaded_file.read(), mime=True)
        if mime_type != 'application/zip':
            messages.error(request,'Invalid file format. Please upload a ZIP file.')

            return redirect('extract_folder')
        
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_path = fs.path(filename)

        # For store the key text value, and the file name of the contain key text value
        text_image_dict = {}

        # Pattern that need to meet the same as key text value
        pattern = r'^[A-Za-z]{3}\s\d{6}$'
        
        # Extract the zip file to a container folder name as user session_id
        session_id_path = os.path.join(os.path.dirname(file_path), str(session_id))
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(session_id_path)
        
        # To get the path of extracted zip file    
        path_zip_folder = fs.path("{}/{}".format(session_id,filename.split(".")[0]))

        # To get the name of the folder after the extraction
        folder_name_zip = (filename.split(".")[0])
        
        # Menelusuri file-file
        for root,dirs,files in os.walk(session_id):
            
            for file in files:

                # Check if the file is an image file
                if file.endswith('.jpg') or file.endswith('.jpeg') or file.endswith('.png') or file.endswith('.txt'):

                    # Construct the image file path
                    image_path = os.path.join(root, file)

                    # Read text from the image using easyOCR
                    # result = reader.readtext(image_path, detail=0)
                    reader = easyocr.Reader(['en'], gpu=False)
                    result = reader.readtext(image_path, detail=0)

                    # For this development phase i'm not using easyOCR, instead i will use basic I/O File function to read each line of the .txt file
                    # with open(image_path, 'r') as buat_file:
                    #     text_list = [line.strip() for line in buat_file]

                    # Store the extracted text as a key and the image filename as a value in the dictionary
                    for text in result:#text_list
                        # Check if the extracted text matches the required pattern
                        if re.match(pattern, text):# or re.match(pattern2, text):
                            if text not in text_image_dict:
                                text_image_dict[text] = [file]
                            else:
                                text_image_dict[text].append(file)

        # Loop through the dictionary to classify and move images based on extracted text
        for text, image_filenames in text_image_dict.items():
            # Create a folder with the extracted text as the folder name
            folder_name = text
            folder_path = os.path.join(path_zip_folder, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            
            # Move the images with the matching extracted text to the folder
            for image_filename in image_filenames:
                source_path = os.path.join(path_zip_folder, image_filename)
                target_path = os.path.join(folder_path, image_filename)
                shutil.move(source_path, target_path)
        
        # Create a .zip file from the folder
        zip_filename = os.path.join(path_zip_folder, f"{folder_name_zip}.zip")
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(path_zip_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, path_zip_folder))


        # Store zip_filename in session
        request.session['zip_filename'] = zip_filename

        return redirect('download_zip')
    return render(request, 'upload.html')

def download_zip (request):

    if request.method == 'POST':
        # Retrieve zip_filename from session
        zip_filename = request.session.get('zip_filename')

        # Untuk membuat 'response request' untuk mendownload .zip file yang akan didownload oleh user
        
        with open(zip_filename, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="{0}"'.format(os.path.basename(zip_filename))

        #Menghapus Container folder user dan .zip file yang user upload
        try:
            container_folder = os.path.dirname(os.path.dirname(zip_filename))
            filename = os.path.basename(zip_filename)
            if os.path.exists(container_folder):
                shutil.rmtree(container_folder)
                print("Folder deleted successfully.")
                
                os.remove(filename)
                
                print("File deleted successfully.")
                
        except OSError as e:
            print(f"Error: {e.filename} - {e.strerror}")

        
        return response
    return render(request, 'success.html')
