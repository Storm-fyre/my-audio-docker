# app.py
import os
import subprocess
import uuid
import shutil
import zipfile

from flask import Flask, render_template, request, send_file, after_this_request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    """
    Show the HTML form for user input (YouTube link, single vs. playlist, best vs. normal).
    """
    return render_template('index.html')


@app.route('/download', methods=['POST'])
def download_audio():
    """
    Handle form submission to download audio via yt-dlp, then serve the file(s).
    Cleans up downloaded files immediately after sending to user.
    """
    # 1. Get form data
    link = request.form.get('link', '').strip()
    video_type = request.form.get('type', 'single').lower()   # "single" or "playlist"
    quality = request.form.get('quality', 'best').lower()     # "best" or "normal"

    if not link:
        return "No link provided.", 400

    # 2. Create a unique temporary folder for this download
    download_id = str(uuid.uuid4())
    download_folder = f"/tmp/{download_id}"
    os.makedirs(download_folder, exist_ok=True)

    # 3. Build the yt-dlp command
    command = ["yt-dlp"]

    if quality == "best":
        command += ["-f", "bestaudio"]
    else:
        # "normal" - limit the rate
        command += ["-f", "bestaudio", "--limit-rate", "512K"]

    # Extract audio
    command += [
        "--extract-audio",
        "--audio-format", "mp3",
        "-o", f"{download_folder}/%(title)s.%(ext)s"
    ]

    # Single or playlist
    if video_type == "playlist":
        command += ["--yes-playlist"]
    else:
        command += ["--no-playlist"]

    command.append(link)

    # 4. Run yt-dlp
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        shutil.rmtree(download_folder, ignore_errors=True)
        return f"Error downloading: {e}", 500

    # 5. Check how many files were downloaded
    downloaded_files = os.listdir(download_folder)
    if not downloaded_files:
        shutil.rmtree(download_folder, ignore_errors=True)
        return "No audio files were downloaded. Possible invalid link or no audio found.", 404

    # AFTER-REQUEST CLEANUP
    @after_this_request
    def remove_files(response):
        try:
            shutil.rmtree(download_folder)
        except:
            pass
        return response

    # 6. Serve single file or zip multiple
    if len(downloaded_files) == 1:
        file_path = os.path.join(download_folder, downloaded_files[0])
        return send_file(file_path, as_attachment=True)
    else:
        zip_name = f"{download_folder}.zip"
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for f in downloaded_files:
                full_path = os.path.join(download_folder, f)
                zipf.write(full_path, arcname=f)

        return send_file(zip_name, as_attachment=True)
