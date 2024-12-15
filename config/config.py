import os

UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

FLASK_PORT = 4729
MAX_FILE_SIZE = 4 * (1024**3)  # 4GB


WHISPER_MODELS = {
    "tiny": "mlx-community/whisper-tiny-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "base-q8": "mlx-community/whisper-base-mlx-8bit",
    "small": "mlx-community/whisper-small-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "turbo": "mlx-community/whisper-large-v3-turbo",
    "large": "mlx-community/whisper-large-v3-mlx",
    "large-q8": "mlx-community/whisper-large-v3-mlx-8bit",
}

ALLOWED_EXTENSIONS = {'m4a', 'mp3', 'aac', 'amr', 'wav'}