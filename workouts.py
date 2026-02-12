import db

def add_workout(user_id, workout_name, category, description, exercises):
    sql = "INSERT INTO workouts (user_id, workout_name, category, description) VALUES (?, ?, ?, ?)"
    db.execute(sql, [user_id, workout_name, category, description])
    workout_id = db.last_insert_id()

    if exercises:
        _insert_exercises(workout_id, exercises)

    return workout_id

def get_user_workouts(user_id):
    sql = """
        SELECT id, workout_name, category, description, created_at
        FROM workouts
        WHERE user_id = ?
        ORDER BY created_at DESC
    """
    return db.query(sql, [user_id])

def get_all_workouts():
    sql = """
        SELECT workouts.id, workouts.workout_name, workouts.category,
               workouts.description, workouts.created_at,
               users.id AS user_id, users.username
        FROM workouts
        JOIN users ON users.id = workouts.user_id
        ORDER BY workouts.created_at DESC
    """
    return db.query(sql)

def get_workout_exercises(workout_id):
    sql = """
        SELECT exercise_number, category, sets, reps, weight
        FROM exercises
        WHERE workout_id = ?
        ORDER BY exercise_number ASC
    """
    return db.query(sql, [workout_id])

def get_workout(workout_id):
    sql = """
        SELECT id, user_id, workout_name, category, description, created_at
        FROM workouts
        WHERE id = ?
    """
    result = db.query(sql, [workout_id])
    if len(result) == 1:
        return result[0]
    return None

def get_workout_with_user(workout_id):
    sql = """
        SELECT workouts.id, workouts.user_id, workouts.workout_name,
               workouts.category, workouts.description, workouts.created_at,
               users.username
        FROM workouts
        JOIN users ON users.id = workouts.user_id
        WHERE workouts.id = ?
    """
    result = db.query(sql, [workout_id])
    if len(result) == 1:
        return result[0]
    return None

def update_workout(workout_id, user_id, workout_name, category, description, exercises):
    sql = """
        UPDATE workouts
        SET workout_name = ?, category = ?, description = ?
        WHERE id = ? AND user_id = ?
    """
    db.execute(sql, [workout_name, category, description, workout_id, user_id])

    db.execute("DELETE FROM exercises WHERE workout_id = ?", [workout_id])
    if exercises:
        _insert_exercises(workout_id, exercises)

def search_workouts(keyword):
    like_term = f"%{keyword}%"
    sql = """
        SELECT DISTINCT workouts.id, workouts.workout_name, workouts.category,
               workouts.description, workouts.created_at,
               users.id AS user_id, users.username
        FROM workouts
        JOIN users ON users.id = workouts.user_id
        LEFT JOIN exercises ON exercises.workout_id = workouts.id
        WHERE workouts.workout_name LIKE ?
           OR workouts.description LIKE ?
           OR workouts.category LIKE ?
           OR exercises.category LIKE ?
        ORDER BY workouts.created_at DESC
    """
    return db.query(sql, [like_term, like_term, like_term, like_term])

def _insert_exercises(workout_id, exercises):
    exercise_sql = """
        INSERT INTO exercises (workout_id, exercise_number, category, sets, reps, weight)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    for index, exercise in enumerate(exercises, start=1):
        db.execute(
            exercise_sql,
            [
                workout_id,
                index,
                exercise["category"],
                exercise["sets"],
                exercise["reps"],
                exercise["weight"],
            ],
        )
