import db

def add_workout(user_id, workout_name, description):
    sql = "INSERT INTO workouts (user_id, workout_name, description) VALUES (?, ?, ?)"
    db.execute(sql, [user_id, workout_name, description])

def get_user_workouts(user_id):
    sql = "SELECT id, workout_name, description, created_at FROM workouts WHERE user_id = ? ORDER BY created_at DESC"
    return db.query(sql, [user_id])
