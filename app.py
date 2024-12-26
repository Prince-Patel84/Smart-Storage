import os
import shutil
from pdf2image import convert_from_path
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, send_from_directory, url_for, flash

app = Flask(__name__)
app.secret_key = 'sk13'  # Required for flash messages

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['PREVIEW_FOLDER'] = 'previews/'  # Separate folder for previews
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg', 'txt', 'docx', 'zip', 'rar'}

# Create necessary folders if they don't exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['PREVIEW_FOLDER']]:
    if not os.path.exists(folder):
        os.makedirs(folder)

#Upload Password
UPLOAD_PASSWORD = "u13"
DELETE_PASSWORD = "d13"
RENAME_PASSWORD = "r13"
CREATE_PASSWORD = "c13"
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
@app.route('/')
def home():
    return render_template('home.html')

# Route to create a new folder
@app.route('/create_folder', methods=['POST'])
def create_folder():
    password = request.form.get('password_c')
    if password == CREATE_PASSWORD:
        folder_name = request.form.get('folder_name')
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        return redirect(url_for('view_folders'))
    else:
        return redirect(url_for('view_folders'))

# Route to view all folders

@app.route('/view_folders')
def view_folders():
    folders = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], f))]
    return render_template('view_folders.html', folders=folders)

# Route to upload files to a specific folder
@app.route('/upload/<folder>', methods=['GET', 'POST'])
def upload_file(folder):
    if request.method == 'POST':
        password = request.form.get('password')
        
        # Check if the password is correct
        if password == UPLOAD_PASSWORD:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
                file.save(os.path.join(folder_path, filename))

                if filename.endswith('.pdf'):
                    # Generate PDF preview
                    preview_path = os.path.join(app.config['PREVIEW_FOLDER'], f"{folder}_{filename}.png")
                    if not os.path.exists(preview_path):  # Generate preview only if it doesn't exist
                        images = convert_from_path(os.path.join(folder_path, filename), first_page=1, last_page=1)
                        images[0].save(preview_path, 'PNG')

                flash("File uploaded successfully!", 'success')
                return redirect(url_for('view_folder', folder=folder))
            else:
                flash("Invalid file type. Only PDF files are allowed.", 'danger')
        # else:
            # flash("Incorrect password!", 'danger')
    return render_template('upload_file.html', folder=folder)


# Route to view files in a folder
@app.route('/view_folder/<folder>')
def view_folder(folder):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    files = os.listdir(folder_path)

    # Create a list of file details including preview links
    file_details = []
    for file in files:
        # if file.endswith('.pdf'):  # Handle only PDF files
            preview_url = url_for('get_preview', folder_name=folder, filename=file)
            file_details.append({
                'name': file,
                'preview_url': preview_url,  # Include both folder_name and filename
                'download_url': url_for('download_file', folder_name=folder, filename=file),
            })
    return render_template('view_folder.html', files=file_details, folder=folder)


@app.route('/preview/<folder_name>/<filename>')
def get_preview(folder_name, filename):
    # List of supported image extensions
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    
    # Check if the file is an image
    if any(filename.endswith(ext) for ext in image_extensions):
        preview_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name, filename)
        
        # Check if the image file exists
        if os.path.exists(preview_path):
            return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], folder_name), filename)
    
    # If it's a PDF, generate a preview
    preview_path = os.path.join(app.config['PREVIEW_FOLDER'], f"{folder_name}_{filename}.png")
    if filename.endswith(".pdf"):
        # Generate a preview for the PDF file (already shown in your code)
        if not os.path.exists(preview_path):  # Generate preview only if it doesn't exist
            images = convert_from_path(os.path.join(app.config['UPLOAD_FOLDER'], folder_name, filename), first_page=1, last_page=1)
            images[0].save(preview_path, 'PNG')
        
        return send_from_directory(app.config['PREVIEW_FOLDER'], f"{folder_name}_{filename}.png", mimetype='image/png')

    return "Preview not available", 404

# Route to download files
@app.route('/download/<folder_name>/<filename>')
def download_file(folder_name, filename):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    return send_from_directory(folder_path, filename, as_attachment=True)

# Route to delete a file
@app.route('/delete/<folder>/<filename>', methods=['POST'])
def delete_file(folder, filename):
    # Password check
    password = request.form.get('password')
    correct_password = DELETE_PASSWORD  # Replace with your actual password logic

    if password != correct_password:
        flash('Incorrect password! File not deleted.', 'error')
        return redirect(url_for('view_folder', folder=folder))

    # File path and preview path
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
    preview_path = os.path.join(app.config['PREVIEW_FOLDER'], f"{folder}_{filename}.png")

    # Check if file exists and delete
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f'File "{filename}" deleted successfully!', 'success')

        # Check if a preview exists and delete
        if os.path.exists(preview_path):
            os.remove(preview_path)
            flash(f'Preview for "{filename}" deleted successfully!', 'success')
    else:
        flash(f'File "{filename}" not found!', 'error')

    return redirect(url_for('view_folder', folder=folder))


# Route to delete a folder
@app.route('/delete_folder/<folder_name>', methods=['POST'])
def delete_folder(folder_name):
    # Password check
    password = request.form.get('password')
    correct_password = DELETE_PASSWORD  # Replace with your actual password logic

    if password != correct_password:
        flash('Incorrect password! Folder not deleted.', 'error')
        return redirect(url_for('view_folders'))

    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    preview_folder_path = os.path.join(app.config['PREVIEW_FOLDER'])

    if os.path.exists(folder_path):
        # Remove the folder and its contents
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            preview_path = os.path.join(preview_folder_path, f"{folder_name}_{filename}.png")
            
            # Delete the file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete the preview file
            if os.path.exists(preview_path):
                os.remove(preview_path)

        # After deleting all files, remove the empty folder
        shutil.rmtree(folder_path)
        flash(f'Folder "{folder_name}" and its contents deleted successfully!', 'success')
    else:
        flash(f'Folder "{folder_name}" not found!', 'error')

    return redirect(url_for('view_folders'))

@app.route('/rename_file/<folder>/<filename>', methods=['POST'])
def rename_file(folder, filename):
    password = request.form.get('password_file')
    correct_password = RENAME_PASSWORD  # Replace with actual password logic
    
    if password == correct_password:
        new_name = request.form.get('new_name')
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        old_file_path = os.path.join(folder_path, filename)
        new_file_path = os.path.join(folder_path, new_name)

        # Check if the file exists
        if os.path.exists(old_file_path):
            os.rename(old_file_path, new_file_path)  # Rename the file
            flash(f'File "{filename}" renamed to "{new_name}"!', 'success')
            
            # Check if a preview exists and rename it
            preview_path = os.path.join(app.config['PREVIEW_FOLDER'], f"{folder}_{filename}.png")
            new_preview_path = os.path.join(app.config['PREVIEW_FOLDER'], f"{folder}_{new_name}.png")
            if os.path.exists(preview_path):
                os.rename(preview_path, new_preview_path)  # Rename the preview image
                flash(f'Preview for file "{filename}" renamed to "{new_name}"!', 'success')
        else:
            flash(f'File "{filename}" not found!', 'error')
    else:
        flash('Incorrect Password!', 'error')
    
    return redirect(url_for('view_folder', folder=folder))



@app.route('/rename_folder/<folder>', methods=['POST'])
def rename_folder(folder):
    password = request.form.get('password')
    correct_password = RENAME_PASSWORD  # Replace with actual password logic
    
    if password != correct_password:
        flash('Incorrect password! Folder not renamed.', 'error')
        return redirect(url_for('view_folders'))

    new_name = request.form.get('new_name')
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    new_folder_path = os.path.join(app.config['UPLOAD_FOLDER'], new_name)

    # Check if the folder exists
    if os.path.exists(folder_path):
        os.rename(folder_path, new_folder_path)  # Rename the folder
        flash(f'Folder "{folder}" renamed to "{new_name}"!', 'success')
        
        # Check if preview exists for the folder and rename it
        preview_path = os.path.join(app.config['PREVIEW_FOLDER'], f"{folder}_preview.png")
        new_preview_path = os.path.join(app.config['PREVIEW_FOLDER'], f"{new_name}_preview.png")
        if os.path.exists(preview_path):
            os.rename(preview_path, new_preview_path)  # Rename the preview image
            flash(f'Preview for folder "{folder}" renamed to "{new_name}"!', 'success')
    else:
        flash(f'Folder "{folder}" not found!', 'error')
    
    return redirect(url_for('view_folders'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

