import os
import yt_dlp
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile
import mimetypes
import http.cookiejar
import subprocess
import json
import re

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
TEMP_DIR = tempfile.gettempdir()
COOKIES_DIR = os.path.join(app.instance_path, 'cookies') if hasattr(app, 'instance_path') else os.path.join(os.getcwd(), 'instance', 'cookies')
os.makedirs(COOKIES_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cookies-status', methods=['GET'])
def cookies_status():
    youtube_exists = os.path.exists(os.path.join(COOKIES_DIR, 'youtube_cookies.txt'))
    instagram_exists = os.path.exists(os.path.join(COOKIES_DIR, 'instagram_cookies.txt'))
    return jsonify({
        'youtube': youtube_exists,
        'instagram': instagram_exists
    })

@app.route('/api/upload-cookies', methods=['POST'])
def upload_cookies():
    platform = request.form.get('platform', '').lower()

    if platform not in ['youtube', 'instagram']:
        return jsonify({'error': 'Invalid platform. Use: youtube or instagram'}), 400

    if 'cookies' not in request.files:
        return jsonify({'error': 'No cookies file provided'}), 400

    file = request.files['cookies']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        cookies_path = os.path.join(COOKIES_DIR, f'{platform}_cookies.txt')
        file.save(cookies_path)
        return jsonify({
            'success': True,
            'message': f'{platform.capitalize()} cookies uploaded successfully!',
            'platform': platform
        })
    except Exception as e:
        return jsonify({'error': f'Failed to upload cookies: {str(e)}'}), 500

@app.route('/api/remove-cookies', methods=['POST'])
def remove_cookies():
    platform = request.json.get('platform', '').lower()

    if platform not in ['youtube', 'instagram']:
        return jsonify({'error': 'Invalid platform'}), 400

    try:
        cookies_path = os.path.join(COOKIES_DIR, f'{platform}_cookies.txt')
        if os.path.exists(cookies_path):
            os.remove(cookies_path)
            return jsonify({'success': True, 'message': f'{platform.capitalize()} cookies removed'})
        return jsonify({'error': 'No cookies found for this platform'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    if not url.startswith(('http://', 'https://')):
        return jsonify({'error': 'Invalid URL format'}), 400

    try:
        is_youtube = any(domain in url for domain in ['youtube.com', 'youtu.be'])
        is_instagram = 'instagram.com' in url

        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            },
        }

        # Add cookies if available
        youtube_cookies = os.path.join(COOKIES_DIR, 'youtube_cookies.txt')
        instagram_cookies = os.path.join(COOKIES_DIR, 'instagram_cookies.txt')

        if is_youtube and os.path.exists(youtube_cookies):
            ydl_opts['cookiefile'] = youtube_cookies

        if is_instagram and os.path.exists(instagram_cookies):
            ydl_opts['cookiefile'] = instagram_cookies

        # YouTube-specific configuration
        if is_youtube:
            ydl_opts['format'] = 'best[height<=720]/best'
            ydl_opts['socket_timeout'] = 60
            ydl_opts['retries'] = 10
            ydl_opts['skip_unavailable_fragments'] = True
            ydl_opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['web', 'android'],
                    'player_skip': ['js'],
                }
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

                return jsonify({
                    'success': True,
                    'filename': os.path.basename(filename),
                    'path': filename,
                    'title': info.get('title', 'download')
                })
            except Exception as inner_e:
                # Try alternative Instagram method
                if is_instagram and 'login required' in str(inner_e).lower():
                    return try_instagram_alternative(url)
                raise

    except Exception as e:
        error_msg = str(e)

        # Handle specific platform errors
        if 'Instagram' in error_msg and ('login required' in error_msg or 'rate-limit' in error_msg or 'not available' in error_msg):
            return jsonify({
                'error': 'Instagram is blocking this download.',
                'details': 'Instagram blocks automated downloads. Try these alternatives:\n1. Upload cookies from an authenticated Instagram session\n2. Use https://www.instagram.com/p/[POST_ID]/ format instead\n3. Try downloading directly from the video file if available\n4. Use external Instagram downloader tools',
                'code': 'INSTAGRAM_BLOCKED'
            }), 429

        if 'youtube' in error_msg.lower() or (is_youtube and 'Sign in' in error_msg):
            return jsonify({
                'error': '⚠️ YouTube is blocking this server (cloud IP)',
                'details': '<strong>Solution: Upload YouTube cookies</strong><br>1. Click "🍪 Manage Cookies" → YouTube tab<br>2. Export cookies from youtube.com using Cookie-Editor extension<br>3. Upload the .txt file<br><br><strong>Why?</strong> YouTube blocks automated downloads from cloud servers for security. Your cookies authenticate the request as a real user.',
                'code': 'YOUTUBE_BOT_CHECK'
            }), 429

        if 'No such file or directory' in error_msg or 'does not appear to be a valid' in error_msg:
            return jsonify({'error': 'Invalid URL or content not available'}), 400

        return jsonify({'error': f'Download failed: {error_msg[:150]}'}), 400

@app.route('/api/file/<path:filename>', methods=['GET'])
def get_file(filename):
    try:
        filepath = os.path.join(TEMP_DIR, secure_filename(filename))
        if os.path.exists(filepath):
            mimetype, _ = mimetypes.guess_type(filepath)
            return send_file(filepath, as_attachment=True, mimetype=mimetype)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
