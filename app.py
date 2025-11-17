from flask import Flask, send_file, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import datetime
import os
import io
import random
import time

app = Flask(__name__)

def create_ai_image(prompt, steps=20, guidance=7.5):
    """Create a simulated AI-generated image with visual elements based on prompt"""
    width, height = 512, 512
    
    # Create background with animated gradient
    img = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(img)
    
    # Time-based seed for consistent but varied results
    seed = hash(prompt) % 1000
    
    # Create dynamic gradient based on prompt
    for y in range(height):
        # Use prompt hash to create consistent but unique gradients
        r = int(50 + 100 * abs(hash(f"red{seed}{y}") % 100) / 100)
        g = int(50 + 100 * abs(hash(f"green{seed}{y}") % 100) / 100)
        b = int(100 + 100 * abs(hash(f"blue{seed}{y}") % 100) / 100)
        draw.line([(0, y), (width, y)], fill=(r, g, b), width=1)
    
    # Draw elements based on prompt keywords
    prompt_lower = prompt.lower()
    
    # Sky elements
    if any(word in prompt_lower for word in ['sunset', 'sunrise', 'dawn', 'dusk']):
        # Draw sun
        sun_x = width // 2
        sun_y = height // 3
        draw.ellipse([sun_x-40, sun_y-40, sun_x+40, sun_y+40], fill='orange', outline='red', width=3)
        
        # Sun rays
        for angle in range(0, 360, 30):
            rad = angle * 3.14159 / 180
            draw.line([
                sun_x, sun_y,
                sun_x + 70 * math.cos(rad), sun_y + 70 * math.sin(rad)
            ], fill='yellow', width=2)
    
    if any(word in prompt_lower for word in ['mountain', 'mountains', 'alps']):
        # Draw mountains
        for i in range(3):
            peak_x = width // 4 * (i + 1)
            peak_y = 150 + (i * 20)
            base_y = height - 50
            draw.polygon([
                (peak_x - 80, base_y),
                (peak_x, peak_y),
                (peak_x + 80, base_y)
            ], fill=f'hsl({120 + i*10}, 70%, 30%)')
    
    if any(word in prompt_lower for word in ['water', 'ocean', 'sea', 'lake', 'river']):
        # Draw water
        for i in range(5):
            wave_y = height - 100 + i * 15
            for x in range(0, width, 30):
                wave_height = 5 * math.sin(x/30 + i) + 3
                draw.ellipse([
                    x, wave_y - wave_height,
                    x + 25, wave_y + wave_height
                ], fill='lightblue', outline='blue')
    
    if any(word in prompt_lower for word in ['forest', 'tree', 'trees', 'wood']):
        # Draw trees
        for i in range(5):
            tree_x = 100 + i * 80
            tree_trunk_y = height - 50
            tree_top_y = height - 150
            # Trunk
            draw.rectangle([tree_x-5, tree_trunk_y, tree_x+5, tree_top_y+30], fill='brown')
            # Leaves
            draw.ellipse([tree_x-25, tree_top_y, tree_x+25, tree_top_y+50], fill='green')
    
    if any(word in prompt_lower for word in ['city', 'building', 'skyscraper', 'urban']):
        # Draw buildings
        for i in range(6):
            building_x = 50 + i * 70
            building_height = random.randint(100, 200)
            building_width = 40
            draw.rectangle([
                building_x, height - building_height,
                building_x + building_width, height - 50
            ], fill='darkgray')
            # Windows
            for floor in range(3):
                for col in range(2):
                    window_x = building_x + 5 + col * 15
                    window_y = height - building_height + 20 + floor * 25
                    draw.rectangle([window_x, window_y, window_x+10, window_y+15], fill='yellow')
    
    # Add informational text
    try:
        # Try to use a larger font if available
        font = ImageFont.truetype("Arial", 16)
    except:
        try:
            font = ImageFont.load_default()
        except:
            font = None
    
    # Text background
    draw.rectangle([10, height-120, width-10, height-10], fill=(0, 0, 0, 128))
    
    # Text content
    lines = [
        "AI Generated Image",
        f"Prompt: {prompt[:40]}{'...' if len(prompt) > 40 else ''}",
        f"Steps: {steps} | Guidance: {guidance}",
        f"Time: {datetime.datetime.now().strftime('%H:%M:%S')}"
    ]
    
    text_y = height - 110
    for line in lines:
        if font:
            draw.text((20, text_y), line, fill='white', font=font)
        else:
            draw.text((20, text_y), line, fill='white')
        text_y += 25
    
    return img

# Fallback math functions
import math

@app.route('/')
def serve_index():
    return send_file('index.html')

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get('prompt', 'A beautiful landscape')
        steps = int(data.get('steps', 20))
        guidance = float(data.get('guidance', 7.5))
        
        print(f"🎨 Generating image for: {prompt}")
        print(f"⚙️ Settings: {steps} steps, {guidance} guidance")
        
        # Create the AI image
        start_time = time.time()
        image = create_ai_image(prompt, steps, guidance)
        generation_time = time.time() - start_time
        
        # Ensure outputs directory exists
        os.makedirs('outputs', exist_ok=True)
        
        # Save image with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"outputs/image_{timestamp}.png"
        image.save(filename)
        print(f"✅ Image saved: {filename}")
        
        # Log the generation
        log_entry = f"{timestamp} | Prompt: {prompt} | Steps: {steps} | Guidance: {guidance} | Time: {generation_time:.2f}s\n"
        with open("outputs/generation_log.txt", "a") as f:
            f.write(log_entry)
        
        # Convert to bytes for response
        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        
        print(f"🎉 Generation completed in {generation_time:.2f} seconds")
        return send_file(img_io, mimetype='image/png')
        
    except Exception as e:
        print(f"❌ Error in generate_image: {e}")
        import traceback
        traceback.print_exc()
        
        # Create a simple error image
        error_img = Image.new('RGB', (512, 512), color='red')
        draw = ImageDraw.Draw(error_img)
        draw.text((50, 200), "Error Generating Image", fill='white')
        draw.text((50, 230), "Please try again", fill='white')
        draw.text((50, 260), str(e)[:100], fill='white')
        
        img_io = io.BytesIO()
        error_img.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "AI Image Generator",
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/test')
def test_image():
    """Test endpoint to verify image generation works"""
    try:
        img = Image.new('RGB', (200, 200), color='blue')
        draw = ImageDraw.Draw(img)
        draw.ellipse([50, 50, 150, 150], fill='red')
        draw.text((60, 80), "TEST OK", fill='white')
        
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create outputs directory
    os.makedirs('outputs', exist_ok=True)
    
    print("🚀 Starting AI Image Generator Server...")
    print("📁 Outputs directory ready")
    print("🌐 Server running on http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
