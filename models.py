from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_points = db.Column(db.Integer, default=0)

    records = db.relationship('DailyRecord', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    rewards = db.relationship('Reward', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def today_record(self):
        return DailyRecord.query.filter_by(
            user_id=self.id, record_date=date.today()
        ).first()

    def streak_days(self):
        """计算连续打卡天数"""
        records = DailyRecord.query.filter_by(user_id=self.id)\
            .order_by(DailyRecord.record_date.desc()).all()
        if not records:
            return 0
        streak = 0
        from datetime import timedelta
        check_date = date.today()
        for r in records:
            if r.record_date == check_date:
                streak += 1
                check_date -= timedelta(days=1)
            elif r.record_date == check_date - timedelta(days=1):
                # 如果今天没打卡但昨天打了，连续天数从昨天算
                if streak == 0:
                    streak = 1
                    check_date -= timedelta(days=1)
                else:
                    break
            else:
                break
        return streak


class DailyRecord(db.Model):
    __tablename__ = 'daily_record'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    record_date = db.Column(db.Date, nullable=False, default=date.today)

    diet_score = db.Column(db.Integer, default=0)
    diet_note = db.Column(db.Text, default='')

    sleep_score = db.Column(db.Integer, default=0)
    sleep_note = db.Column(db.Text, default='')

    mood_score = db.Column(db.Integer, default=0)
    mood_note = db.Column(db.Text, default='')

    exercise_score = db.Column(db.Integer, default=0)
    exercise_note = db.Column(db.Text, default='')

    total_points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'record_date', name='uq_user_date'),
    )

    def calculate_points(self):
        self.total_points = self.diet_score + self.sleep_score + self.mood_score + self.exercise_score
        return self.total_points

    def to_dict(self):
        return {
            'date': self.record_date.strftime('%Y-%m-%d'),
            'diet': self.diet_score,
            'sleep': self.sleep_score,
            'mood': self.mood_score,
            'exercise': self.exercise_score,
            'total': self.total_points,
        }


class Reward(db.Model):
    __tablename__ = 'reward'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    points_required = db.Column(db.Integer, nullable=False)
    is_achieved = db.Column(db.Boolean, default=False)
    redeemed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
