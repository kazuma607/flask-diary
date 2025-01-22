from app import db

# データベースに 'examples' カラムを追加するスクリプト
with db.engine.connect() as conn:
    conn.execute("ALTER TABLE diary_entry ADD COLUMN examples TEXT")

