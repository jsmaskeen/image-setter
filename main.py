from flask import Flask, render_template, request, session, redirect, url_for,jsonify,send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS, cross_origin
from uuid import uuid4
from dotenv import load_dotenv
import img2pdf
import os
from PIL import Image
import shutil
load_dotenv()


DPI = 600
A4_WIDTH, A4_HEIGHT = 29.7 * DPI / 2.54, 21.0 * DPI / 2.54  # A4 size in pixels (landscape, DPI DPI)
IMAGE_HEIGHT_CM = 9
IMAGE_HEIGHT_PIXELS = int(IMAGE_HEIGHT_CM * DPI / 2.54)  # Convert cm to pixels
MARGIN_CM = 1
MARGIN_PIXELS = int(MARGIN_CM * DPI / 2.54)
SPACING_PIXELS = 20

def resize_image(image, new_height):
    width, height = image.size
    new_width = int((new_height / height) * width)
    return image.resize((new_width, new_height), Image.LANCZOS)

def process_images(images):
    a4_image = Image.new('RGB', (int(A4_WIDTH), int(A4_HEIGHT)), 'white')

    x_offset = MARGIN_PIXELS
    y_offset = MARGIN_PIXELS

    for index, image_path in enumerate(images):
        image = Image.open(image_path)
        sz = image.size
        if sz[0]>sz[1]:
            image = image.rotate(90,expand=True)
            
        resized_image = resize_image(image, IMAGE_HEIGHT_PIXELS)
        
        if x_offset + resized_image.width > A4_WIDTH - MARGIN_PIXELS:
            x_offset = MARGIN_PIXELS
            y_offset += IMAGE_HEIGHT_PIXELS + SPACING_PIXELS

        if y_offset + IMAGE_HEIGHT_PIXELS > A4_HEIGHT - MARGIN_PIXELS:
            break

        a4_image.paste(resized_image, (x_offset, y_offset))
        x_offset += resized_image.width + SPACING_PIXELS

        if (index + 1) % 5 == 0:
            x_offset = MARGIN_PIXELS
            y_offset += IMAGE_HEIGHT_PIXELS + SPACING_PIXELS

    return a4_image

def main(folder_path):
    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)]
    batches = [files[i:i + 10] for i in range(0, len(files), 10)]

    for batch_index, batch in enumerate(batches):
        a4_image = process_images(batch)
        a4_image.save(f'{tmp}/converted/batch_{batch_index + 1}.jpg', 'JPEG')
        
def convert_to_pdf(fp):
    imgs =[]
    for files in os.listdir(f'{tmp}/{fp}'):
        imgs.append(f'{tmp}/{fp}/{files}')
    with open(f"{tmp}/output.pdf","wb") as f:
	    f.write(img2pdf.convert(imgs))



app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"
app.secret_key = str(uuid4())
tmp = os.getenv('tmp')

@app.route("/")
@cross_origin()
def index():
    return render_template('home.html',secret_message=os.getenv('message'))

@app.route('/upload', methods=['POST'])
@cross_origin()
def upload_file():
    if not os.path.exists(f'{tmp}/imgs'):
        try:
            os.mkdir(f'{tmp}')
        except FileExistsError:
            pass
        try:
            os.mkdir(f'{tmp}/imgs')
        except FileExistsError:
            pass
    if not os.path.exists(f'{tmp}/converted'):
        try:
            os.mkdir(f'{tmp}')
        except FileExistsError:
            pass
        try:
            os.mkdir(f'{tmp}/converted')
        except FileExistsError:
            pass
    files = request.files.getlist("file[]")
    for file in files:
        filename = secure_filename(file.filename)
        file.save(f'{tmp}/imgs/{filename}')
    
    
    main(f'{tmp}/imgs')
    convert_to_pdf('converted')
    
    shutil.rmtree(f'{tmp}/imgs')
    shutil.rmtree(f'{tmp}/converted')
    
    return send_file(f'{tmp}/output.pdf',as_attachment=True)

@app.errorhandler(404)
@cross_origin()
def page_not_found(e):
    return "Not found bbye", 404

if __name__ == "__main__":
    app.run(debug=True)
