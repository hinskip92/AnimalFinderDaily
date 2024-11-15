import os
from flask import render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app import db
from models import Task, AnimalSpotting
from services.gpt_service import generate_tasks, recognize_animal
from services.location_service import get_location_info

def register_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/tasks')
    def tasks():
        return render_template('tasks.html')

    @app.route('/api/tasks', methods=['POST'])
    def get_tasks():
        data = request.json
        lat = data.get('latitude')
        lng = data.get('longitude')
        
        if not lat or not lng:
            return jsonify({'error': 'Location required'}), 400
            
        location_info = get_location_info(lat, lng)
        tasks = generate_tasks(location_info)
        
        return jsonify(tasks)

    @app.route('/api/recognize', methods=['POST'])
    def recognize():
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.root_path, 'static/uploads', filename)
        file.save(filepath)
        
        result = recognize_animal(filepath)
        
        return jsonify(result)
