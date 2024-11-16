import os
from datetime import datetime, timedelta
from flask import render_template, request, jsonify, current_app, url_for, abort
from werkzeug.utils import secure_filename
from app import db
from models import Task, AnimalSpotting, Badge, spotting_badges  # Add spotting_badges import
from services.gpt_service import generate_tasks, recognize_animal
from services.location_service import get_location_info
from services.achievement_service import AchievementService

def register_routes(app):
    # Ensure uploads directory exists
    uploads_dir = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)

    @app.route('/')
    def index():
        # Get today's tasks
        today = datetime.utcnow().date()
        current_tasks = Task.query.filter(
            Task.expires_at >= today,
            Task.created_at <= today + timedelta(days=1)
        ).all()
        
        # Get recent badges (last 5)
        recent_badges = Badge.query.join(spotting_badges)\
            .join(AnimalSpotting)\
            .order_by(spotting_badges.c.awarded_at.desc())\
            .limit(5).all()
        
        return render_template('index.html', 
                             current_tasks=current_tasks,
                             recent_badges=recent_badges)

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
        try:
            if not request.is_json:
                return jsonify({
                    'error': 'Invalid request format. Expected JSON.'
                }), 400

            data = request.get_json()
            if not data:
                return jsonify({
                    'error': 'Missing request data.'
                }), 400

            lat = data.get('latitude')
            lng = data.get('longitude')
            
            if lat is None or lng is None:
                return jsonify({
                    'error': 'Location coordinates are required. Please enable location access.'
                }), 400
                
            location_info = get_location_info(lat, lng)
            if 'error' in location_info:
                return jsonify({
                    'error': f'Failed to get location information: {location_info["error"]}'
                }), 500
                
            tasks = generate_tasks(location_info)
            return jsonify(tasks)
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            current_app.logger.error(f"Error generating tasks: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'Failed to generate tasks. Please try again later.'
            }), 500

    @app.route('/api/recognize', methods=['POST'])
    def recognize():
        try:
            if not request.files:
                return jsonify({
                    'error': 'No files were uploaded. Please capture or upload an image.'
                }), 400

            file = request.files.get('image') or request.files.get('camera_image')
            if not file:
                return jsonify({
                    'error': 'No image file provided. Please capture or upload an image.'
                }), 400

            if not file.filename:
                return jsonify({
                    'error': 'No selected file. Please choose an image file.'
                }), 400
                
            if not file.content_type or not file.content_type.startswith('image/'):
                return jsonify({
                    'error': 'Invalid file type. Please upload an image file (JPEG, PNG, etc.).'
                }), 400
                
            # Create a unique filename with timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(f"{timestamp}_{file.filename}")
            filepath = os.path.join(current_app.root_path, 'static/uploads', filename)
            
            # Save the file
            file.save(filepath)
            
            try:
                # Process the image
                result = recognize_animal(filepath)
                
                # Create spotting record and set attributes
                spotting = AnimalSpotting()
                spotting.task_id = request.form.get('task_id')
                spotting.image_path = filename
                spotting.recognition_result = result["animal"]
                spotting.detailed_info = result["details"]
                spotting.location = request.form.get('location')
                spotting.generate_share_id()
                
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
                # Clean up file if processing failed
                try:
                    os.remove(filepath)
                except:
                    pass
                raise e
                
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            current_app.logger.error(f"Error processing image: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'Failed to process image. Please try again with a different image.'
            }), 500

    @app.route('/api/badges', methods=['GET'])
    def get_badges():
        try:
            badges = Badge.query.all()
            return jsonify([{
                'name': badge.name,
                'description': badge.description,
                'icon_class': badge.icon_class
            } for badge in badges])
        except Exception as e:
            current_app.logger.error(f"Error fetching badges: {str(e)}", exc_info=True)
            return jsonify({'error': 'Failed to fetch badges'}), 500

    @app.route('/api/tasks/current')
    def get_current_tasks():
        today = datetime.utcnow().date()
        current_tasks = Task.query.filter(
            Task.expires_at >= today,
            Task.created_at <= today + timedelta(days=1)
        ).all()
        
        tasks_data = [{
            'id': task.id,
            'animal': task.animal,
            'task_type': task.task_type,
            'completed': bool(task.spottings),
            'progress': len(task.spottings) if task.task_type == 'daily' else None
        } for task in current_tasks]
        
        return jsonify({'tasks': tasks_data})

    # Initialize default badges when the app starts
    with app.app_context():
        AchievementService.initialize_default_badges()
