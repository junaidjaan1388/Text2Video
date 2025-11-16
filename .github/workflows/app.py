from flask import Flask, send_file, request, jsonify
from PIL import Image, ImageDraw
import datetime
import os
import io
import random

app = Flask(__name__)

def create_ai_image(prompt):
    """Create a simulated AI-generated image"""
    width, height = 512, 512
    
    # Create background with gradient
    img = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(img)
    
    # Create gradient background
    for y in range(height):
        r = int(50 + 100 * (y / height))
        g = int(50 + 100 * ((height - y) / height))
        b = int(100 + 100 * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b), width=1)
    
    # Draw shapes based on prompt keywords
    if 'sunset' in prompt.lower():
        draw.ellipse([width//2-80, 100, width//2+80, 260], fill='orange')
    if 'mountain' in prompt.lower():
        points = [(100, height-100), (width//2, 150), (width-100, height-100)]
        draw.polygon(points, fill='darkgreen')
    if 'water' in prompt.lower() or 'ocean' in prompt.lower():
        for i in range(3):
            y_pos = height - 150 + i*20
            draw.line([(0, y_pos), (width, y_pos)], fill='lightblue', width=3)
    if 'forest' in prompt.lower():
        for i in range(5):
            x = random.randint(50, width-100)
            draw.rectangle([x, height-200, x+30, height-100], fill='green')
    
    # Add text
    lines = [
        "AI Generated Image",
        f"Prompt: {prompt}",
        f"Time: {datetime.datetime.now().strftime('%H:%M:%S')}",
        "Simulated AI Art"
    ]
    
    y_pos = height - 180
    for line in lines:
        # Shadow
        draw.text((52, y_pos+2), line, fill='black')
        # Main text
        draw.text((50, y_pos), line, fill='white')
        y_pos += 25
    
    return img

@app.route('/')
def serve_index():
    return send_file('index.html')

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get('prompt', 'A beautiful landscape')
        model = data.get('model', 'runwayml/stable-diffusion-v1-5')
        steps = data.get('steps', 20)
        guidance = data.get('guidance', 7.5)
        
        print(f"Generating image: {prompt}")
        
        # Create the image
        image = create_ai_image(prompt)
        
        # Ensure outputs directory exists
        os.makedirs('outputs', exist_ok=True)
        
        # Save to outputs
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"outputs/image_{timestamp}.png"
        image.save(filename)
        
        # Log generation
        with open("outputs/generation_log.txt", "a") as f:
            f.write(f"{timestamp} | {prompt} | {filename}\n")
        
        # Convert to bytes for response
        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        
        print(f"✅ Image generated: {filename}")
        return send_file(img_io, mimetype='image/png')
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # Return error image
        error_img = Image.new('RGB', (512, 512), color='red')
        draw = ImageDraw.Draw(error_img)
        draw.text((50, 250), "Error generating image", fill='white')
        img_io = io.BytesIO()
        error_img.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')

@app.route('/images')
def list_images():
    """List all generated images"""
    try:
        images = [f for f in os.listdir('outputs') if f.endswith('.png')]
        return jsonify({"images": images, "count": len(images)})
    except:
        return jsonify({"images": [], "count": 0})

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting AI Image Generator Server...")
    # Ensure outputs directory exists
    os.makedirs('outputs', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False)
