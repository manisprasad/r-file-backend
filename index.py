from flask import Flask, request, send_file, jsonify
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black
from reportlab.lib.pagesizes import letter
from io import BytesIO
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

def update_first_page(input_pdf, temp_pdf, name="Manish Prasad", roll_no="41523056"):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    
    # Process only the first page
    first_page = reader.pages[0]
    
    # Get page dimensions
    width = float(first_page.mediabox.upper_right[0])
    height = float(first_page.mediabox.upper_right[1])
    
    # Create overlay with new text
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    
    # Set font and color
    can.setFont("Helvetica-Bold", 12)
    can.setFillColor(black)
    
    # Coordinates for the name and roll number (adjust as needed)
    name_x, name_y = 180, 163  # Adjust these based on your PDF layout
    roll_x, roll_y = 180, 147   # Adjust these based on your PDF layout
    
    # Draw white rectangles to cover old text
    can.setFillColorRGB(1, 1, 1)  # White
    can.rect(name_x - 5, name_y - 5, 80, 20, fill=1, stroke=0)
    can.rect(roll_x - 5, roll_y - 5, 60, 20, fill=1, stroke=0)
    
    # Draw new text
    can.setFillColor(black)
    can.drawString(name_x, name_y, name)
    can.drawString(roll_x, roll_y, roll_no)
    
    can.save()
    
    # Merge overlay with first page
    packet.seek(0)
    overlay = PdfReader(packet)
    first_page.merge_page(overlay.pages[0])
    
    # Add all pages to writer (first page modified, others unchanged)
    writer.add_page(first_page)
    for page in reader.pages[1:]:
        writer.add_page(page)
    
    # Save temporary output
    with open(temp_pdf, "wb") as f:
        writer.write(f)

def trim_and_add_text(input_pdf, output_pdf, text="Vaibhav Prasad 41523056"):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for page_num, page in enumerate(reader.pages):
        # Get original page size
        width = float(page.mediabox.upper_right[0])
        height = float(page.mediabox.upper_right[1])
        
        # 1. Trim bottom 25px
        page.mediabox.lower_left = (0, 25)
        page.cropbox.lower_left = (0, 25)
        new_height = height - 25

        # 2. Create overlay with text
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, new_height))
        
        # Set text properties
        can.setFont("Helvetica-Bold", 14)
        can.setFillColor(black)
        
        # Calculate text position
        text_width = can.stringWidth(text, "Helvetica-Bold", 14)
        x_pos = (width - text_width) / 2
        y_pos = 28  # 25px from the new bottom

        # Optional: Draw white background behind the text
        can.setFillColorRGB(1, 1, 1)  # White background
        can.rect(x_pos - 2, y_pos - 2, text_width + 4, 18, fill=1, stroke=0)
        can.setFillColor(black)  # Back to black text
        
        # Draw the text
        can.drawString(x_pos, y_pos, text)
        can.save()

        # 3. Merge the overlay
        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]
        page.merge_page(overlay_page)

        writer.add_page(page)

    # Write the output file
    with open(output_pdf, "wb") as output_file:
        writer.write(output_file)


@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Welcome to the PDF Processing API!"})

@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    # Get data from request
    data = request.get_json()
    if not data or 'name' not in data or 'roll_no' not in data:
        return jsonify({"error": "Name and roll_no are required"}), 400
    
    name = data['name']
    roll_no = data['roll_no']
    footer_text = f"{name} {roll_no}"
    
    # File paths
    input_path = "private_compressed.pdf"  # Make sure this file exists in your directory
    temp_file = "temp_processed.pdf"
    output_path = "FinalOutput.pdf"
    
    try:
        # First create a temporary file with the first page updated
        update_first_page(input_path, temp_file, name, roll_no)
        
        # Then process all pages with the trimming and footer
        trim_and_add_text(temp_file, output_path, footer_text)
        
        # Send the processed file
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"processed_{name.replace(' ', '_')}_{roll_no}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temporary files
        for file_path in [temp_file, output_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass

if __name__ == '__main__':
    app.run(debug=True)