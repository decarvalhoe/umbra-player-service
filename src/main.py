"""
umbra-player-service - Service de gestion des profils et données des joueurs
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    
    # Configuration
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', '0') == '1'
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'service': 'umbra-player-service'
            },
            'message': 'Service en bonne santé'
        }), 200
    
    # TODO: Ajouter les routes spécifiques au service
    
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', '5001'))
    app.run(host='0.0.0.0', port=port, debug=True)
