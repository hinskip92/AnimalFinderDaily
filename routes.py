import os
from flask import render_template, request, jsonify, current_app, url_for, abort
from werkzeug.utils import secure_filename
from app import db
from models import Task, AnimalSpotting, Badge
from services.gpt_service import generate_tasks, recognize_animal
from services.location_service import get_location_info
from services.achievement_service import AchievementService

def register_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/tasks')
    def tasks():
        return render_template('tasks.html')

    @app.route('/badges')
    def badges():
        all_badges = Badge.query.all()
        return render_template('badges.html', badges=all_badges)
        
    @app.route('/share/<share_id>')
    def share(share_id):
        spotting = AnimalSpotting.query.filter_by(share_id=share_id).first_or_404()
        return render_template('share.html', spotting=spotting)

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
        
        # Create spotting record
        task_id = request.form.get('task_id')
        if task_id:
            task = Task.query.get(task_id)
            spotting = AnimalSpotting(
                task=task,
                image_path=filename,
                recognition_result=result,
                location=request.form.get('location')
            )
            spotting.generate_share_id()  # Generate unique share ID
            db.session.add(spotting)
            db.session.commit()
            
            # Check and award achievements
            new_badges = AchievementService.check_achievements(spotting)
            badge_names = [badge.name for badge in new_badges]
            
            return jsonify({
                'result': result,
                'new_badges': badge_names,
                'share_url': url_for('share', share_id=spotting.share_id, _external=True)
            })
            
        return jsonify({'result': result})

    @app.route('/api/badges', methods=['GET'])
    def get_badges():
        badges = Badge.query.all()
        return jsonify([{
            'name': badge.name,
            'description': badge.description,
            'icon_class': badge.icon_class
        } for badge in badges])

    # Initialize default badges when the app starts
    with app.app_context():
        AchievementService.initialize_default_badges()
