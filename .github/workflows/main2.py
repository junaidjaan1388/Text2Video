name: AI Image Generator

on:
  workflow_dispatch:
    inputs:
      prompt:
        description: 'Image generation prompt'
        required: true
        default: 'A beautiful sunset over mountains, digital art'

jobs:
  image-generator:
    runs-on: ubuntu-latest
    timeout-minutes: 25
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        cd web-app
        pip install -r requirements.txt

    - name: Install Ngrok
      run: |
        wget -q -O ngrok.tgz https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
        tar -xzf ngrok.tgz
        chmod +x ngrok
        sudo mv ngrok /usr/local/bin/
        ngrok version

    - name: Setup Ngrok authentication
      run: |
        ngrok authtoken "${{ secrets.NGROK_AUTH_TOKEN }}"
        echo "✅ Ngrok configured"

    - name: Create outputs directory
      run: mkdir -p web-app/outputs

    - name: Start server with health check
      run: |
        cd web-app
        python app.py &
        SERVER_PID=$!
        echo "SERVER_PID=$SERVER_PID" >> $GITHUB_ENV
        
        # Wait for server with retries
        echo "⏳ Waiting for server to start..."
        for i in {1..30}; do
          if curl -s http://localhost:5000/health > /dev/null 2>&1; then
            echo "✅ Server is healthy after $((i*2)) seconds"
            break
          fi
          if [ $i -eq 30 ]; then
            echo "❌ Server failed to start"
            exit 1
          fi
          sleep 2
        done
        
        # Test image generation
        echo "🧪 Testing image generation..."
        curl -X POST http://localhost:5000/generate \
          -H "Content-Type: application/json" \
          -d '{"prompt":"test image", "steps":20, "guidance":7.5}' \
          -o test.png 2>/dev/null && echo "✅ Test image generated" || echo "❌ Test failed"

    - name: Start Ngrok tunnel
      run: |
        echo "🌐 Starting Ngrok tunnel..."
        ngrok http 5000 --log=stdout > ngrok.log 2>&1 &
        echo "NGROK_PID=$!" >> $GITHUB_ENV
        sleep 10

    - name: Get public URL
      id: ngrok_url
      run: |
        echo "🔗 Getting Ngrok URL..."
        for i in {1..10}; do
          URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o 'https://[^"]*\.ngrok\.io' | head -1)
          if [ -n "$URL" ]; then
            echo "ngrok_url=$URL" >> $GITHUB_OUTPUT
            echo "✅ Public URL: $URL"
            break
          fi
          sleep 3
        done

    - name: Show connection info
      run: |
        echo ""
        echo "✨ ================================="
        echo "✨   AI IMAGE GENERATOR READY!"
        echo "✨ ================================="
        echo "✨ URL: ${{ steps.ngrok_url.outputs.ngrok_url }}"
        echo "✨ Test: ${{ steps.ngrok_url.outputs.ngrok_url }}/test"
        echo "✨ Health: ${{ steps.ngrok_url.outputs.ngrok_url }}/health"
        echo "✨ ================================="

    - name: Keep service running
      run: |
        echo "⏰ Service active for 20 minutes..."
        echo "🌐 Your generator: ${{ steps.ngrok_url.outputs.ngrok_url }}"
        
        for i in {1..120}; do
          echo "[$(date +%H:%M:%S)] Running... ($((i/6))m $((i%6*10))s)"
          
          # Monitor every 30 seconds
          if [ $((i % 3)) -eq 0 ]; then
            if curl -s http://localhost:5000/health > /dev/null; then
              count=$(find web-app/outputs -name "*.png" 2>/dev/null | wc -l)
              echo "   📊 Status: Healthy | Images: $count"
            else
              echo "   ❌ Status: Server down"
            fi
          fi
          
          sleep 10
        done

    - name: Upload generated images
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: ai-images
        path: web-app/outputs/
        retention-days: 30

    - name: Cleanup
      if: always()
      run: |
        echo "🧹 Cleaning up..."
        kill $SERVER_PID 2>/dev/null || true
        pkill ngrok 2>/dev/null || true
        echo "✅ Cleanup complete"
