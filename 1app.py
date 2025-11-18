from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import sys
import os
from diffusers import DiffusionPipeline
import torch
from PIL import Image
import io
import base64
import uuid

class TextToImageHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.pipeline = None
        super().__init__(*args, **kwargs)
    
    def initialize_pipeline(self):
        """Initialize the diffusion pipeline"""
        if self.pipeline is None:
            print("Loading diffusion pipeline...")
            # Using a smaller model for faster loading
            self.pipeline = DiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                use_safetensors=True
            )
            if torch.cuda.is_available():
                self.pipeline = self.pipeline.to("cuda")
            print("Pipeline loaded successfully!")
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/health':
            self.send_health_response()
            return
        elif self.path == '/status':
            self.send_status_response()
            return
        return super().do_GET()
    
    def do_POST(self):
        if self.path == '/generate':
            self.handle_generate()
        else:
            self.send_error(404, "Endpoint not found")
    
    def send_health_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {
            "status": "healthy",
            "service": "Text-to-Image Diffuser",
            "gpu_available": torch.cuda.is_available()
        }
        self.wfile.write(json.dumps(response).encode())
    
    def send_status_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {
            "model_loaded": self.pipeline is not None,
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "service": "ready" if self.pipeline else "loading"
        }
        self.wfile.write(json.dumps(response).encode())
    
    def handle_generate(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            prompt = data.get('prompt', '')
            if not prompt:
                self.send_error(400, "Prompt is required")
                return
            
            # Initialize pipeline if not already done
            self.initialize_pipeline()
            
            # Generate image
            print(f"Generating image for prompt: {prompt}")
            image = self.pipeline(
                prompt=prompt,
                num_inference_steps=20,  # Reduced for speed
                guidance_scale=7.5,
                width=512,
                height=512
            ).images[0]
            
            # Convert image to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "success": True,
                "image": f"data:image/png;base64,{img_str}",
                "prompt": prompt,
                "id": str(uuid.uuid4())
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"Error generating image: {str(e)}")
            self.send_error(500, f"Generation failed: {str(e)}")
    
    def log_message(self, format, *args):
        print(f"[{self.client_address[0]}] {format % args}")

def run(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, TextToImageHandler)
    print(f'🚀 Text-to-Image Server running on port {port}')
    print(f'📁 Serving files from current directory')
    print(f'⚡ GPU available: {torch.cuda.is_available()}')
    print(f'🔮 Access the app at: http://localhost:{port}')
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == '--port' else 8080
    run(port)
