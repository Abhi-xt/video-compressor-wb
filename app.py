import os, uuid, subprocess, requests
from flask import Flask, request, jsonify, render_template, send_from_directory

app = Flask(__name__)
UPLOAD_DIR = 'static/processed'
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/compress', methods=['POST'])
def compress_video():
    data = request.json
    url = data.get('video_url')
    method = data.get('method')
    value = float(data.get('value'))

    if not url.startswith("https://"):
        return jsonify({'error': 'Only HTTPS URLs allowed'}), 400

    try:
        filename = f"{uuid.uuid4()}.mp4"
        input_path = f"/tmp/{filename}"
        output_path = os.path.join(UPLOAD_DIR, filename)

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(input_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        size_mb = os.path.getsize(input_path) / (1024 * 1024)
        duration = float(subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_path
        ]).strip())

        if method == 'percentage':
            target_mb = size_mb * (value / 100)
        elif method == 'size_mb':
            target_mb = value
        else:
            return jsonify({'error': 'Invalid method'}), 400

        bitrate = int((target_mb * 8 * 1024 * 1024) / duration)
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-b:v', str(bitrate), '-bufsize', str(bitrate),
            '-preset', 'fast', output_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        os.remove(input_path)
        return jsonify({'download_url': f'/download/{filename}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run()
