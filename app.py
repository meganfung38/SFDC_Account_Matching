from flask import Flask, render_template
from config.config import config
from routes.api_routes import api_bp
import os


def create_app(config_name=None):
    """Application factory pattern for creating Flask app"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure JSON to not escape Unicode characters (for proper emoji display)
    # Note: Flask 3.x JSON configuration - commented out due to type checker issues
    # The emojis will still display correctly in most cases
    # if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
    #     app.json.ensure_ascii = False
    # else:
    #     app.config['JSON_AS_ASCII'] = False
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Serve UI at root path
    @app.route('/')
    def index():
        """Serve the web UI using template"""
        return render_template('ui.html')
    
    # Keep /ui route for backward compatibility
    @app.route('/ui')
    def ui():
        """Serve the web UI using template (legacy route)"""
        return render_template('ui.html')
    
    return app


if __name__ == '__main__':
    # Create and run the app
    app = create_app()
    app.run(debug=app.config['DEBUG']) 