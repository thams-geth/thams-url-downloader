# Thams URL Downloader

A simple, fast web app to download videos, images, and files from any URL. Supports YouTube, Instagram, TikTok, Twitter, and more.

## Features

✅ Download YouTube videos  
✅ Download Instagram reels & posts  
✅ Download TikTok videos  
✅ Download Twitter videos  
✅ Download images and documents from any URL  
✅ Clean, modern UI  
✅ No account required  

## Tech Stack

- **Backend**: Python Flask
- **Downloader**: yt-dlp (handles multiple platforms)
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Ready for Render, Railway, Heroku

## Local Installation & Running

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/thams-url-downloader.git
cd thams-url-downloader
```

### 2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python app.py
```

The app will be available at `http://localhost:5000`

## Deployment Options

### Option 1: Deploy to Render (Recommended - Free tier available)

1. Push your code to GitHub
2. Go to [render.com](https://render.com)
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Deploy!

### Option 2: Deploy to Railway

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app)
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Python and deploys automatically

### Option 3: Deploy to Heroku

1. Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Login: `heroku login`
3. Create app: `heroku create thams-url-downloader`
4. Add Procfile:
   ```
   web: gunicorn app:app
   ```
5. Deploy:
   ```bash
   git push heroku main
   ```

## Usage

1. Open the web app
2. Paste any URL in the input field
3. Click "Download"
4. Wait for processing (30 seconds to 2 minutes depending on file size)
5. Click "Download File" to save

## Supported URLs

- YouTube: `https://youtube.com/watch?v=...`
- Instagram: `https://instagram.com/p/...` or reels
- TikTok: `https://tiktok.com/@.../video/...`
- Twitter: `https://twitter.com/.../status/...`
- Any direct file URL: `https://example.com/image.jpg`

## Limitations

- Files must be under 500MB
- Processing may take 30 seconds to 2 minutes
- Some platforms may have rate limiting
- Downloaded files are stored temporarily

## Adding Gunicorn (for production)

Add to `requirements.txt`:
```
gunicorn==21.2.0
```

## Environment Variables (Optional)

Create a `.env` file:
```
FLASK_ENV=production
```

## Troubleshooting

**"Invalid URL or content not available"**
- URL might be invalid or the platform blocked the request
- Try again in a few moments (rate limit)

**"Download failed"**
- The file might be too large
- The website might have restrictions
- Check your internet connection

## License

MIT License - feel free to use, modify, and distribute

## Support

If you encounter issues:
1. Check the error message carefully
2. Try with a different URL
3. Ensure your internet connection is stable
4. Some platforms may require additional authentication

---

Made with ❤️ by Thams
