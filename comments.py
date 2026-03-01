import db

def get_workout_comments(workout_id):
    sql = """
        SELECT comments.id, comments.workout_id, comments.user_id, 
               comments.comment_text, comments.created_at, users.username
        FROM comments
        JOIN users ON users.id = comments.user_id
        WHERE comments.workout_id = ?
        ORDER BY comments.created_at DESC
    """
    return db.query(sql, [workout_id])

def add_comment(workout_id, user_id, comment_text):
    sql = """
        INSERT INTO comments (workout_id, user_id, comment_text)
        VALUES (?, ?, ?)
    """
    db.execute(sql, [workout_id, user_id, comment_text])

def delete_comment(comment_id, user_id):
    # Only allow deletion by the user who created the comment
    sql = "DELETE FROM comments WHERE id = ? AND user_id = ?"
    db.execute(sql, [comment_id, user_id])

def get_comment(comment_id):
    sql = """
        SELECT id, workout_id, user_id, comment_text, created_at
        FROM comments
        WHERE id = ?
    """
    result = db.query(sql, [comment_id])
    if len(result) == 1:
        return result[0]
    return None
