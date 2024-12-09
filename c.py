from flask import Flask, render_template, jsonify
import telegram
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

class TelegramVideoStreamer:
    def __init__(self, bot_token, chat_id):
        """
        Initialize Telegram Video Streamer
        
        :param bot_token: Telegram Bot Token
        :param chat_id: Chat ID to stream videos from
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = telegram.Bot(token=bot_token)
        self.video_list = []

    async def fetch_videos(self):
        """
        Fetch all video files from the specified chat
        """
        self.video_list.clear()
        async with self.bot:
            async for message in self.bot.get_chat(self.chat_id).get_history():
                if message.video or message.document:
                    # Check if it's a video file
                    video = message.video or message.document
                    
                    # Get video file link
                    file = await video.get_file()
                    file_url = file.file_path
                    
                    # Add to video list
                    self.video_list.append({
                        'id': len(self.video_list) + 1,
                        'url': file_url,
                        'file_name': video.file_name or f"video_{len(self.video_list) + 1}",
                        'mime_type': video.mime_type
                    })
        
        return self.video_list

# Global variables to store video list
VIDEO_LIST = []

# Initialize Flask app
app = Flask(__name__)

# Telegram Bot configuration
BOT_TOKEN = '7340782041:AAFO8_BOYR4-xSwEnDgCFwLVV9XDZ8yV-L0'
CHAT_ID = 1728061231

@app.route('/')
def index():
    """
    Render the main page with video player
    """
    global VIDEO_LIST
    if not VIDEO_LIST:
        # Fetch videos synchronously
        async def get_videos():
            streamer = TelegramVideoStreamer(BOT_TOKEN, CHAT_ID)
            return await streamer.fetch_videos()
        
        VIDEO_LIST = asyncio.run(get_videos())
    
    return render_template('index.html', videos=VIDEO_LIST)

@app.route('/videos')
def get_videos():
    """
    API endpoint to get list of videos
    """
    global VIDEO_LIST
    if not VIDEO_LIST:
        # Fetch videos synchronously
        async def get_videos():
            streamer = TelegramVideoStreamer(BOT_TOKEN, CHAT_ID)
            return await streamer.fetch_videos()
        
        VIDEO_LIST = asyncio.run(get_videos())
    
    return jsonify(VIDEO_LIST)

# HTML Template
def create_html_template():
    html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram Video Streamer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .container {
            display: flex;
            gap: 20px;
        }
        .video-list {
            width: 300px;
            background-color: white;
            border-radius: 8px;
            padding: 10px;
            max-height: 80vh;
            overflow-y: auto;
        }
        .video-player {
            flex-grow: 1;
            background-color: black;
        }
        .video-item {
            cursor: pointer;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        .video-item:hover {
            background-color: #f0f0f0;
        }
        video {
            max-width: 100%;
            max-height: 80vh;
        }
        h1 {
            text-align: center;
            color: #333;
        }
    </style>
</head>
<body>
    <h1>Telegram Video Streamer</h1>
    <div class="container">
        <div class="video-list" id="videoList">
            <!-- Video list will be populated dynamically -->
        </div>
        <div class="video-player">
            <video id="videoPlayer" controls>
                Your browser does not support the video tag.
            </video>
        </div>
    </div>

    <script>
        // Fetch and display videos
        async function fetchVideos() {
            try {
                const response = await fetch('/videos');
                const videos = await response.json();
                
                const videoList = document.getElementById('videoList');
                const videoPlayer = document.getElementById('videoPlayer');
                
                // Clear previous list
                videoList.innerHTML = '';
                
                // Populate video list
                videos.forEach(video => {
                    const videoItem = document.createElement('div');
                    videoItem.classList.add('video-item');
                    videoItem.textContent = video.file_name;
                    videoItem.onclick = () => {
                        videoPlayer.src = video.url;
                        videoPlayer.play();
                    };
                    videoList.appendChild(videoItem);
                });

                // Autoplay first video if available
                if (videos.length > 0) {
                    videoPlayer.src = videos[0].url;
                }
            } catch (error) {
                console.error('Error fetching videos:', error);
            }
        }

        // Initial fetch
        fetchVideos();
    </script>
</body>
</html>
    '''
    
    # Create templates directory if it doesn't exist
    import os
    os.makedirs('templates', exist_ok=True)
    
    # Write HTML to file
    with open('templates/index.html', 'w') as f:
        f.write(html_content)

# Create HTML template before running the app
create_html_template()

# Requirements file
def create_requirements_file():
    requirements = '''
flask
python-telegram-bot
python-telegram
'''
    with open('requirements.txt', 'w') as f:
        f.write(requirements)

# Create requirements file
create_requirements_file()

# Main run block
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

# Installation Instructions:
# 1. Create a virtual environment (optional but recommended)
# 2. Install requirements: pip install -r requirements.txt
# 3. Run the application: python app.py
# 4. Open browser and go to http://localhost:5000
'''
Deployment Notes:
- Requires Flask
- Uses Telegram Bot API for video streaming
- Simple, responsive web interface
- Supports multiple video formats
- Easy to customize and extend
'''
