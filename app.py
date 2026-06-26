import os
import yt_dlp
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile
import mimetypes
import http.cookiejar

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
TEMP_DIR = tempfile.gettempdir()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    if not url.startswith(('http://', 'https://')):
        return jsonify({'error': 'Invalid URL format'}), 400

    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['web'],
                    'player_skip': ['js', 'webpage']
                }
            }
        }

        # Check if URL is YouTube
        is_youtube = any(domain in url for domain in ['youtube.com', 'youtu.be'])
        if is_youtube:
            ydl_opts['format'] = 'best[height<=720]'
            ydl_opts['socket_timeout'] = 60
            ydl_opts['retries'] = 5
            ydl_opts['skip_unavailable_fragments'] = True

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            return jsonify({
                'success': True,
                'filename': os.path.basename(filename),
                'path': filename,
                'title': info.get('title', 'download')
            })

    except Exception as e:
        error_msg = str(e)

        # Handle specific platform errors
        if 'Instagram' in error_msg and ('login required' in error_msg or 'rate-limit' in error_msg):
            return jsonify({'error': 'Instagram requires authentication. Try: 1) Use a direct video link, 2) Try after 1 hour, or 3) Use instagram-specific downloader'}), 429

        if 'youtube' in error_msg.lower() and 'sign in' in error_msg.lower():
            return jsonify({'error': 'YouTube requires verification. Try: 1) Wait 5 minutes, 2) Use a different YouTube video, or 3) Try a different URL format'}), 429

        if 'No such file or directory' in error_msg or 'does not appear to be a valid' in error_msg:
            return jsonify({'error': 'Invalid URL or content not available'}), 400

        return jsonify({'error': f'Download failed: {error_msg[:100]}'}), 400

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
