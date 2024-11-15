from datetime import datetime, timedelta
from models import Badge, AnimalSpotting, db

class AchievementService:
    @staticmethod
    def check_achievements(spotting):
        """Check and award achievements for a new animal spotting"""
        badges = []
        
        # First spotting badge
        first_spot_badge = Badge.query.filter_by(criteria='first_spot').first()
        if first_spot_badge and AnimalSpotting.query.count() == 1:
            badges.append(first_spot_badge)
        
        # Daily streak badges
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        daily_spottings = AnimalSpotting.query.filter(
            AnimalSpotting.spotted_at >= yesterday,
            AnimalSpotting.spotted_at < today + timedelta(days=1)
        ).count()
        
        if daily_spottings >= 5:
            daily_5_badge = Badge.query.filter_by(criteria='daily_5').first()
            if daily_5_badge:
                badges.append(daily_5_badge)
        
        # Weekly task completion badge
        if spotting.task and spotting.task.task_type == 'weekly':
            weekly_complete_badge = Badge.query.filter_by(criteria='weekly_complete').first()
            if weekly_complete_badge:
                badges.append(weekly_complete_badge)
        
        # Award badges
        for badge in badges:
            if badge not in spotting.badges:
                spotting.badges.append(badge)
        
        db.session.commit()
        return badges

    @staticmethod
    def initialize_default_badges():
        """Create default badges if they don't exist"""
        default_badges = [
            {
                'name': 'First Spotter',
                'description': 'Completed your first animal spotting!',
                'icon_class': 'fa-solid fa-star',
                'criteria': 'first_spot'
            },
            {
                'name': 'Daily Explorer',
                'description': 'Spotted 5 animals in one day',
                'icon_class': 'fa-solid fa-compass',
                'criteria': 'daily_5'
            },
            {
                'name': 'Weekly Champion',
                'description': 'Completed a weekly challenge',
                'icon_class': 'fa-solid fa-trophy',
                'criteria': 'weekly_complete'
            }
        ]
        
        for badge_data in default_badges:
            if not Badge.query.filter_by(criteria=badge_data['criteria']).first():
                badge = Badge(**badge_data)
                db.session.add(badge)
        
        db.session.commit()
