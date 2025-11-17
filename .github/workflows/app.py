from flask import Flask, send_file, request, jsonify, send_from_directory
from diffusers import StableDiffusionPipeline
import torch
from PIL import Image, ImageDraw
import datetime
import os
import io
import time

app = Flask(__name__)

# Global model variable
pipe = None
model_loaded = False

def load_model():
    global pipe, model_loaded
    try:
        if model_loaded:
            return True
            
        print("🔄 Loading Stable Diffusion model...")
        start_time = time.time()
        
        # Use smaller model for faster loading
        model_id = "runwayml/stable-diffusion-v1-5"
        
        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float32,
            use_safetensors=True,
            safety_checker=None,  # Disable safety checker for speed
            requires_safety_checker=False
        )
        pipe = pipe.to("cpu")
        pipe.enable_attention_slicing()  # Reduce memory usage
        
        load_time = time.time() - start_time
        model_loaded = True
        print(f"✅ Model loaded in {load_time:.1f} seconds")
        return True
        
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False

def create_placeholder_image(prompt, status="Loading model..."):
    """Create a placeholder image while model loads"""
    img = Image.new('RGB', (512, 512), color=(40, 40, 80))
    draw = ImageDraw.Draw(img)
    
    # Draw border
    draw.rectangle([10, 10, 502, 502], outline=(100, 100, 200), width=3)
    
    # Add text
    lines = [
        "🎨 AI Image Generator",
        "",
        f"Prompt: {prompt}",
        "",
        status,
        "",
        "Powered by Stable Diffusion",
        f"Time: {datetime.datetime.now().strftime('%H:%M:%S')}"
    ]
    
    y_pos = 150
    for line in lines:
        text_width = len(line) * 9
        x_pos = (512 - text_width) // 2
        draw.text((x_pos, y_pos), line, fill=(200, 200, 255))
        y_pos += 30
    
    return img

@app.route('/')
def serve_index():
    return send_file('index.html')

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get('prompt', 'a beautiful landscape')
        steps = data.get('steps', 20)
        guidance = data.get('guidance', 7.5)
        
        print(f"🎨 Generating: {prompt}")
        
        # Load model if not loaded
        if not load_model():
            img = create_placeholder_image(prompt, "Model loading failed")
            img_io = io.BytesIO()
            img.save(img_io, 'PNG')
            img_io.seek(0)
            return send_file(img_io, mimetype='image/png')
        
        # Generate image with progress
        print("⚡ Generating image...")
        start_time = time.time()
        
        with torch.no_grad():
            image = pipe(
                prompt=prompt,
                num_inference_steps=steps,
                guidance_scale=guidance,
                generator=torch.Generator(device="cpu").manual_seed(int(time.time()))
            ).images[0]
        
        gen_time = time.time() - start_time
        print(f"✅ Image generated in {gen_time:.1f} seconds")
        
        # Save image
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"outputs/image_{timestamp}.png"
        image.save(filename)
        
        # Log generation
        with open("outputs/generation_log.txt", "a") as f:
            f.write(f"{timestamp} | {prompt} | {steps} steps | {guidance} guidance | {filename}\n")
        
        # Convert to bytes for response
        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
        
    except Exception as e:
        print(f"❌ Generation error: {e}")
        # Return error image
        img = create_placeholder_image("Error", f"Error: {str(e)[:50]}...")
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "model_loaded": model_loaded,
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/status')
def status():
    return jsonify({
        "model_loaded": model_loaded,
        "service": "Stable Diffusion API",
        "version": "1.0"
    })

if __name__ == '__main__':
    # Ensure outputs directory exists
    os.makedirs('outputs', exist_ok=True)
    
    print("🚀 Starting Text-to-Image Server...")
    print("📦 Pre-loading model (this may take 2-3 minutes)...")
    
    # Pre-load model in background
    def load_model_async():
        load_model()
    
    import threading
    thread = threading.Thread(target=load_model_async)
    thread.daemon = True
    thread.start()
    
    app.run(host='0.0.0.0', port=5000, debug=False)
