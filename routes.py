import os
from datetime import datetime
from flask import render_template, request, jsonify, current_app, url_for, abort
from werkzeug.utils import secure_filename
from app import db
from models import Task, AnimalSpotting, Badge
from services.gpt_service import generate_tasks, recognize_animal
from services.location_service import get_location_info
from services.achievement_service import AchievementService

def register_routes(app):
    # Ensure uploads directory exists
    uploads_dir = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)

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
        try:
            if 'image' not in request.files and 'camera_image' not in request.files:
                return jsonify({'error': 'No image provided'}), 400
                
            file = request.files.get('image') or request.files.get('camera_image')
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
                
            # Create a unique filename with timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(f"{timestamp}_{file.filename}")
            filepath = os.path.join(current_app.root_path, 'static/uploads', filename)
            
            # Ensure the uploads directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save the file
            file.save(filepath)
            
            # Process the image
            result = recognize_animal(filepath)
            
            # Create spotting record
            task_id = request.form.get('task_id')
            spotting = AnimalSpotting(
                task_id=task_id,
                image_path=filename,
                recognition_result=result["animal"],
                detailed_info=result["details"],
                location=request.form.get('location')
            )
            spotting.generate_share_id()  # Generate unique share ID
            db.session.add(spotting)
            db.session.commit()
            
            # Check and award achievements
            new_badges = AchievementService.check_achievements(spotting)
            badge_names = [badge.name for badge in new_badges]
            
            return jsonify({
                'result': result["animal"],
                'details': result["details"],
                'new_badges': badge_names,
                'share_url': url_for('share', share_id=spotting.share_id, _external=True)
            })
                
        except Exception as e:
            current_app.logger.error(f"Error processing image: {str(e)}", exc_info=True)
            # Clean up file if it was saved
            if 'filepath' in locals():
                try:
                    os.remove(filepath)
                except:
                    pass
            return jsonify({'error': 'Failed to process image'}), 500

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
