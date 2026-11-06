
from flask import Flask, render_template, request, jsonify
import os
import uuid
from werkzeug.utils import secure_filename

from face_generator import generate_face

app = Flask(__name__)

# Project folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "static", "generated")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Allowed audio formats
ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "webm"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# Homepage
@app.route("/")
def home():
    return render_template("index.html")


# Audio upload and AI face generation
@app.route("/generate", methods=["POST"])

@app.route("/generate", methods=["POST"])
def generate():

    if "audio" not in request.files:
        return jsonify({"error": "No audio file received"}), 400

    audio = request.files["audio"]

    if audio.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(audio.filename):
        return jsonify({"error": "Unsupported audio format"}), 400

    audio_path = None

    try:
        filename = secure_filename(audio.filename)
        unique_id = uuid.uuid4().hex

        audio_filename = f"{unique_id}_{filename}"
        audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)

        audio.save(audio_path)

        image_filename = f"{unique_id}.png"
        image_path = os.path.join(OUTPUT_FOLDER, image_filename)

        # Generate face using the uploaded audio
        generate_face(audio_path, image_path)

        return jsonify({
            "message": "Face generated successfully!",
            "image_url": f"/static/generated/{image_filename}"
        })

    except Exception:
        app.logger.exception("Face generation failed")

        return jsonify({
            "error": "Face generation failed. Check the terminal for details."
        }), 500

    finally:
        # Automatically delete uploaded audio after processing
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                app.logger.info("Temporary audio file deleted.")
            except OSError:
                app.logger.exception("Could not delete temporary audio file.")


if __name__ == "__main__":
    # Disable reloader to avoid loading large AI models twice
    app.run(debug=True, use_reloader=False)
