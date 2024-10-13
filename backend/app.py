from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
import os
from twelvelabs import TwelveLabs
from twelvelabs.models.task import Task
from dotenv import load_dotenv
from generate_data_file import generate_data
import zipfile
from io import BytesIO
app = Flask(__name__)
CORS(app)  # This allows CORS for all domains on all routes

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4'}




app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
     # Get the current working directory
    current_directory = os.getcwd()
    
    # Define the path where you want to save the file
    save_path = os.path.join(current_directory, file.filename)
    
    # Save the file to the current directory
    file.save(save_path)
    
    GENERATED_FOLDER_NAME = generate_data(save_path)
    GENERATED_FOLDER_NAME = 'output/' + GENERATED_FOLDER_NAME
    # if file.filename == '':
    #     return jsonify({'error': 'No selected file'}), 400
    # if file and allowed_file(file.filename):
    #     filename = file.filename
    #     file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    #     return jsonify({'message': 'File uploaded successfully'}), 200
    video_files = [f for f in os.listdir(GENERATED_FOLDER_NAME) if os.path.isfile(os.path.join(GENERATED_FOLDER_NAME, f))]
    
    if not video_files:
        return jsonify({'error': 'No videos generated'}), 400
    
    # Create a zip file in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for video_file in video_files:
            video_path = os.path.join(GENERATED_FOLDER_NAME, video_file)
            zip_file.write(video_path, video_file)

    # Seek to the beginning of the BytesIO buffer
    zip_buffer.seek(0)
    
    # Send the zip file as a response to the frontend
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='videos.zip')

    # return jsonify({'error': 'File type not allowed'}), 400


from flask import Flask, request, jsonify
import os
import subprocess
from werkzeug.utils import secure_filename


# No need to create specific directories; all files will be in the root folder

@app.route('/ai-commentary', methods=['POST'])
def ai_commentary():
    if 'videos' not in request.files:
        return jsonify({'error': 'No video uploaded'}), 400

    # Get all the uploaded video files
    video_files = request.files.getlist('videos')

    # List to store the video paths for concatenation
    video_paths = []

    # Save each uploaded video temporarily
    for idx, video_file in enumerate(video_files):
        filename = secure_filename(f'input_part_{idx}.mp4')
        video_path = os.path.join('/tmp', filename)  # Ensure the path is absolute
        video_file.save(video_path)
        video_paths.append(video_path)

    try:
        # Create a text file listing all the video paths for ffmpeg
        concat_list_path = '/tmp/concat_list.txt'
        with open(concat_list_path, 'w') as f:
            for video_path in video_paths:
                # Write the absolute path to the file
                f.write(f"file '{video_path}'\n")

        # Use FFmpeg to concatenate the videos
        concatenated_video_path = 'input.mp4'
        ffmpeg_concat_command = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_list_path,
            '-c', 'copy', concatenated_video_path
        ]
        subprocess.run(ffmpeg_concat_command, check=True)

        # Run the Python script that generates the narration (output.wav)
        narration_script = 'openai-video_narration_speech.py'
        process = subprocess.Popen(['python3', narration_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Read the output of the process line by line to wait for "Audio file write complete!"
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())  # Log the output
                if "Audio file write complete!" in output:
                    # Simulate pressing '1' programmatically, if needed
                    process.stdin.write('1\n')
                    process.stdin.flush()

        process.wait()  # Ensure the process completes

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, narration_script)

        # Ensure the narration output file (output.wav) exists
        output_audio_path = 'output.wav'
        if not os.path.exists(output_audio_path):
            return jsonify({'error': 'Narration generation failed, output.wav not found.'}), 500

        # Use FFmpeg to merge input.mp4 and output.wav to produce output.mp4
        output_video_path = 'output.mp4'
        ffmpeg_merge_command = [
            'ffmpeg', '-i', concatenated_video_path, '-i', output_audio_path,
            '-c:v', 'copy', '-c:a', 'aac', '-map', '0:v:0', '-map', '1:a:0', output_video_path
        ]
        subprocess.run(ffmpeg_merge_command, check=True)

        # Send the combined video file as a response
        return send_file(output_video_path, mimetype='video/mp4', as_attachment=True, download_name='output.mp4')

    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Error during process: {str(e)}'}), 500
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)


