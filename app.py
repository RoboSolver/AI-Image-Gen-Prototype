import os
import sys
import webbrowser
import threading
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.generator import GenerationManager
from backend.database import Database
from backend.settings_manager import SettingsManager
from backend.image_manager import ImageManager
from backend.provider_manager import ProviderManager

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-me')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = Database()
settings_mgr = SettingsManager()
image_mgr = ImageManager()

# Debug: Check provider manager
pm_test = ProviderManager(settings_mgr)

gen_mgr = GenerationManager(db, settings_mgr, image_mgr)

@app.route('/')
def index():
    return render_template('index.html', settings=settings_mgr.get_all())

@app.route('/settings')
def settings_page():
    return render_template('settings.html', settings=settings_mgr.get_all())

@app.route('/history')
def history_page():
    generations = db.get_all_generations(limit=100)
    return render_template('history.html', generations=generations, settings=settings_mgr.get_all())

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({'success': False, 'error': 'Prompt is required'}), 400
    
    options = {
        'num_images': min(max(int(data.get('num_images', 1)), 1), 9),
        'aspect_ratio': data.get('aspect_ratio', settings_mgr.get('default_aspect_ratio', '1:1')),
        'style': data.get('style', settings_mgr.get('default_style', 'realistic')),
        'resolution': data.get('resolution', settings_mgr.get('default_resolution', '1024x1024')),
        'provider': data.get('provider', settings_mgr.get('default_provider', 'pollinations')),
    }
    
    result = gen_mgr.generate(prompt, options)
    return jsonify(result)

@app.route('/api/providers')
def api_providers():
    return jsonify(gen_mgr.get_provider_status())

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    if request.method == 'GET':
        return jsonify(settings_mgr.get_all())
    data = request.get_json() or {}
    settings_mgr.update(data)
    # Refresh providers in case API key changed
    gen_mgr.refresh_providers()
    return jsonify({'success': True, 'settings': settings_mgr.get_all()})

@app.route('/api/history')
def api_history():
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    generations = db.get_all_generations(limit=limit, offset=offset)
    return jsonify(generations)

@app.route('/api/history/<int:gen_id>', methods=['DELETE'])
def api_delete_history(gen_id):
    db.delete_generation(gen_id)
    return jsonify({'success': True})

@app.route('/api/history/clear', methods=['POST'])
def api_clear_history():
    db.clear_history()
    return jsonify({'success': True})

@app.route('/generated/<path:filename>')
def serve_generated(filename):
    return send_from_directory(image_mgr.base_path, filename)

@app.route('/api/storage')
def api_storage():
    return jsonify(image_mgr.get_storage_info())

@app.route('/api/cleanup', methods=['POST'])
def api_cleanup():
    data = request.get_json() or {}
    days = data.get('days', 30)
    deleted = image_mgr.cleanup_old_images(days)
    return jsonify({'success': True, 'deleted': deleted})

def open_browser():
    time.sleep(1.5)
    port = int(os.getenv('FLASK_PORT', 5000))
    webbrowser.open(f'http://localhost:{port}')

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    if os.getenv('FLASK_ENV') != 'production':
        threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=port, debug=False)