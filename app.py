import os
import uuid
import shutil
import subprocess
from pathlib import Path

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
CONVERTED_DIR = BASE_DIR / "converted"
PALETTE_PATH = BASE_DIR / "palettes" / "4color.png"


ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "bmp",
    "webp",
}


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "change-me"),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        UPLOAD_FOLDER=str(UPLOAD_DIR),
        CONVERTED_FOLDER=str(CONVERTED_DIR),
    )

    for directory in (UPLOAD_DIR, CONVERTED_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    @app.route("/", methods=["GET", "POST"])
    def index():
        download_filename = None
        original_preview = None
        converted_preview = None
        if request.method == "POST":
            file = request.files.get("image")
            if not file or file.filename == "":
                flash("Please choose an image to upload.")
                return redirect(url_for("index"))

            if not _is_allowed(file.filename):
                flash("Unsupported file type. Please upload an image file.")
                return redirect(url_for("index"))

            if not PALETTE_PATH.exists():
                flash("Palette file not found. Place your palette at palettes/4color.png.")
                return redirect(url_for("index"))

            original_name = secure_filename(file.filename)
            upload_name = f"{uuid.uuid4().hex}_{original_name}"
            upload_path = UPLOAD_DIR / upload_name
            file.save(upload_path)

            output_name = f"ecard_{Path(original_name).stem}.jpg"
            unique_output = f"{uuid.uuid4().hex}_{output_name}"
            output_path = CONVERTED_DIR / unique_output

            try:
                _run_imagemagick(upload_path, output_path, PALETTE_PATH)
            except subprocess.CalledProcessError as error:
                flash("Image conversion failed. Please try another image.")
                _log_error(error)
                return redirect(url_for("index"))

            download_filename = unique_output
            original_preview = upload_name
            converted_preview = unique_output

        return render_template(
            "index.html",
            download_filename=download_filename,
            original_preview=original_preview,
            converted_preview=converted_preview,
        )

    @app.route("/converted/<path:filename>")
    def download(filename: str):
        return send_from_directory(
            app.config["CONVERTED_FOLDER"], filename, as_attachment=True
        )

    @app.route("/converted/preview/<path:filename>")
    def converted_preview_file(filename: str):
        return send_from_directory(app.config["CONVERTED_FOLDER"], filename)

    @app.route("/uploads/<path:filename>")
    def uploaded_preview(filename: str):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    return app


def _is_allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _run_imagemagick(input_path: Path, output_path: Path, palette_path: Path) -> None:
    executable = _select_magick()
    command = [
        executable,
        str(input_path),
        "-dither",
        "FloydSteinberg",
        "-remap",
        str(palette_path),
        "-quality",
        "95",
        str(output_path),
    ]
    subprocess.run(command, check=True, capture_output=True)


def _select_magick() -> str:
    for candidate in ("magick", "convert"):
        if shutil.which(candidate):
            return candidate
    raise RuntimeError("ImageMagick executable not found. Install ImageMagick to continue.")


def _log_error(error: subprocess.CalledProcessError) -> None:
    stderr = error.stderr.decode("utf-8", errors="ignore") if error.stderr else ""
    stdout = error.stdout.decode("utf-8", errors="ignore") if error.stdout else ""
    print("ImageMagick command failed:", error)
    if stdout:
        print("STDOUT:", stdout)
    if stderr:
        print("STDERR:", stderr)


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=False)
