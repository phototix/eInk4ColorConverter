# E-Ink Image Converter

Flask-powered web UI that converts user uploads into four-color E-Ink friendly JPEGs using ImageMagick with a custom palette. The interface shows a live preview before upload and a side-by-side comparison after conversion.

## Prerequisites

- Python 3.10+
- [ImageMagick](https://imagemagick.org/) installed (`magick` or `convert` on `PATH`)
- Palette file at `palettes/4color.png`

Install ImageMagick on Ubuntu:

```bash
sudo apt update
sudo apt install imagemagick
```

Create a Python virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the App Locally

1. Place your palette file at `palettes/4color.png`.
2. Export a secret key (optional but recommended):

   ```bash
   export FLASK_SECRET_KEY="$(python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
)"
   ```

3. Start the Flask development server:

   ```bash
   flask --app app run --host 0.0.0.0 --port 8000
   ```

4. Visit `http://SERVER_IP:8000` in a browser.

Converted files remain in `converted/`; uploads are retained in `uploads/` for inline previews.

## Deploying Behind cloudflared (Optional)

If you have a Cloudflare Tunnel, add an ingress rule that points your hostname to the Flask service, restart `cloudflared`, and expose the app securely without opening firewall ports.

```yaml
ingress:
  - hostname: ecard.example.com
    service: http://127.0.0.1:8000
  - service: http_status:404
```

## Conversion Pipeline

Images are processed with Floyd–Steinberg dithering and remapped to the supplied palette:

```bash
magick input.png -dither FloydSteinberg -remap palettes/4color.png -quality 95 ecard_output.jpg
```

If the `magick` shim is unavailable, the app automatically falls back to the legacy `convert` binary.
