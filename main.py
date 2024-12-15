from app import create_app
from config.config import FLASK_PORT

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=FLASK_PORT)