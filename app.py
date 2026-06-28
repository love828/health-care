#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Care - 巧克力囊肿患者健康管理应用
饮食 | 睡眠 | 心情 | 运动 每日打卡积分系统
"""

import os
import sys
from datetime import date, datetime, timedelta

# Windows 编码兼容：确保 Flask 能输出中文
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

from flask import (
    Flask, render_template, redirect, url_for,
    flash, request, jsonify
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)

from models import db, User, DailyRecord, Reward
from quotes import get_quote_of_the_day, get_daily_tips

# ---------------------------------------------------------------------------
# App Factory / Config
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'dc-secret-key-change-in-production-2024'
)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///daily_care.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录后再访问'
login_manager.login_message_category = 'info'


# 确保响应使用 UTF-8 编码
@app.after_request
def fix_encoding(response):
    content_type = response.content_type or ''
    if 'charset' not in content_type and 'text/' in content_type:
        response.content_type = content_type + '; charset=utf-8'
    return response


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def update_user_total_points(user_id):
    """重新计算用户总分（所有打卡记录之和）"""
    total = db.session.query(
        db.func.coalesce(db.func.sum(DailyRecord.total_points), 0)
    ).filter_by(user_id=user_id).scalar()
    user = User.query.get(user_id)
    if user:
        user.total_points = total
        db.session.commit()


# ---------------------------------------------------------------------------
# Routes - Auth
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'欢迎回来，{username}！🌸', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('用户名或密码错误，请重试', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not username or len(username) < 2:
            flash('用户名至少2个字符', 'error')
            return render_template('register.html')
        if len(password) < 4:
            flash('密码至少4个字符', 'error')
            return render_template('register.html')
        if password != confirm:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('用户名已被使用，请换一个', 'error')
            return render_template('register.html')

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('🎉 注册成功！请登录', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已安全退出', 'info')
    return redirect(url_for('login'))


# ---------------------------------------------------------------------------
# Routes - Dashboard
# ---------------------------------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    today_record = current_user.today_record()

    # 每日名言 & 行动建议
    quote_of_the_day = get_quote_of_the_day(today)
    daily_tips = get_daily_tips(today)

    # 最近7天记录
    recent_records = DailyRecord.query.filter_by(
        user_id=current_user.id
    ).order_by(DailyRecord.record_date.desc()).limit(7).all()

    # 本周打卡天数
    week_start = today - timedelta(days=today.weekday())
    week_records = DailyRecord.query.filter(
        DailyRecord.user_id == current_user.id,
        DailyRecord.record_date >= week_start,
        DailyRecord.record_date <= today
    ).count()

    rewards = Reward.query.filter_by(
        user_id=current_user.id, is_achieved=False
    ).order_by(Reward.points_required.asc()).all()

    return render_template(
        'dashboard.html',
        today=today,
        today_record=today_record,
        recent_records=recent_records,
        week_records=week_records,
        streak=current_user.streak_days(),
        rewards=rewards,
        quote_of_the_day=quote_of_the_day,
        daily_tips=daily_tips,
    )


# ---------------------------------------------------------------------------
# Routes - Check-in
# ---------------------------------------------------------------------------

@app.route('/checkin', methods=['GET', 'POST'])
@login_required
def checkin():
    today = date.today()
    record = current_user.today_record()
    is_new = record is None

    if request.method == 'POST':
        if record is None:
            record = DailyRecord(user_id=current_user.id, record_date=today)
            db.session.add(record)

        record.diet_score = min(max(int(request.form.get('diet_score', 0)), 0), 5)
        record.diet_note = request.form.get('diet_note', '').strip()
        record.sleep_score = min(max(int(request.form.get('sleep_score', 0)), 0), 5)
        record.sleep_note = request.form.get('sleep_note', '').strip()
        record.mood_score = min(max(int(request.form.get('mood_score', 0)), 0), 5)
        record.mood_note = request.form.get('mood_note', '').strip()
        record.exercise_score = min(max(int(request.form.get('exercise_score', 0)), 0), 5)
        record.exercise_note = request.form.get('exercise_note', '').strip()

        record.calculate_points()
        db.session.commit()
        update_user_total_points(current_user.id)

        earned = record.total_points
        if is_new:
            flash(f'🎉 今日打卡完成！获得 {earned} 积分', 'success')
        else:
            flash(f'✅ 今日打卡已更新，当前获得 {earned} 积分', 'success')
        return redirect(url_for('dashboard'))

    return render_template('checkin.html', record=record, today=today, is_new=is_new)


# ---------------------------------------------------------------------------
# Routes - History
# ---------------------------------------------------------------------------

@app.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    pagination = DailyRecord.query.filter_by(
        user_id=current_user.id
    ).order_by(DailyRecord.record_date.desc()).paginate(
        page=page, per_page=14, error_out=False
    )
    return render_template('history.html', records=pagination)


# ---------------------------------------------------------------------------
# Routes - Rewards
# ---------------------------------------------------------------------------

@app.route('/rewards', methods=['GET', 'POST'])
@login_required
def rewards():
    if request.method == 'POST':
        action = request.form.get('action', '')

        if action == 'add':
            name = request.form.get('name', '').strip()
            points = request.form.get('points_required', 0, type=int)
            if not name:
                flash('请输入奖励名称', 'error')
            elif points < 1:
                flash('所需积分必须大于0', 'error')
            else:
                reward = Reward(
                    user_id=current_user.id,
                    name=name,
                    points_required=points,
                )
                db.session.add(reward)
                db.session.commit()
                flash(f'🎁 奖励"{name}"设置成功！', 'success')

        elif action == 'redeem':
            reward_id = request.form.get('reward_id', type=int)
            reward = Reward.query.get(reward_id)
            if not reward or reward.user_id != current_user.id:
                flash('奖励不存在', 'error')
            elif reward.is_achieved:
                flash('该奖励已兑换过', 'info')
            elif current_user.total_points < reward.points_required:
                need = reward.points_required - current_user.total_points
                flash(f'积分不足，还需要 {need} 积分 💪', 'error')
            else:
                reward.is_achieved = True
                reward.redeemed_at = datetime.utcnow()
                current_user.total_points -= reward.points_required
                db.session.commit()
                flash(f'🎉 恭喜兑换"{reward.name}"！', 'success')

        elif action == 'delete':
            reward_id = request.form.get('reward_id', type=int)
            reward = Reward.query.get(reward_id)
            if reward and reward.user_id == current_user.id:
                db.session.delete(reward)
                db.session.commit()
                flash('奖励已删除', 'info')

        return redirect(url_for('rewards'))

    pending = Reward.query.filter_by(
        user_id=current_user.id, is_achieved=False
    ).order_by(Reward.points_required.asc()).all()

    achieved = Reward.query.filter_by(
        user_id=current_user.id, is_achieved=True
    ).order_by(Reward.redeemed_at.desc()).all()

    return render_template(
        'rewards.html',
        pending=pending,
        achieved=achieved,
    )


# ---------------------------------------------------------------------------
# API - Statistics (for charts)
# ---------------------------------------------------------------------------

@app.route('/api/stats')
@login_required
def api_stats():
    days = request.args.get('days', 30, type=int)
    days = min(max(days, 7), 90)

    records = DailyRecord.query.filter_by(
        user_id=current_user.id
    ).order_by(DailyRecord.record_date.desc()).limit(days).all()

    return jsonify([r.to_dict() for r in reversed(records)])


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    import sys
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    print('Daily Care 应用已启动！', flush=True)
    print('访问地址: http://127.0.0.1:5000', flush=True)
    app.run(debug=True, host='0.0.0.0')
