import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import openai

# GPT-4 APIキーの設定
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flaskアプリの設定
app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# データベース初期化
db = SQLAlchemy(app)

# データベースモデルの定義
class DiaryEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(10), nullable=False)
    correction = db.Column(db.Text)

# データベースの作成
with app.app_context():
    db.create_all()

# チャット機能
@app.route("/chat/<int:entry_id>", methods=["GET", "POST"])
def chat(entry_id):
    entry = DiaryEntry.query.get(entry_id)
    if not entry:
        return "指定された日記が見つかりません。", 404

    if request.method == "POST":
        user_message = request.json.get("message", "")
        if not user_message:
            return jsonify({"error": "メッセージが空です。"}), 400

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "あなたは日本語学習者の会話練習パートナーです。返答は30文字以内にまとめてください。内容はCEFR A2レベルでわかりやすくしてください。"},
                    {"role": "user", "content": entry.content},
                    {"role": "user", "content": user_message}
                ]
            )
            assistant_message = response["choices"][0]["message"]["content"]
            return jsonify({"reply": assistant_message})
        except Exception as e:
            print(f"Error during GPT chat: {e}")
            return jsonify({"error": "GPTとの会話中にエラーが発生しました。"}), 500

    # 初期のGPTのメッセージ生成
    try:
        initial_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは日本語学習者の会話練習パートナーです。返答は30文字以内にまとめてください。内容はCEFR A2レベルでわかりやすくしてください。"},
                {"role": "user", "content": entry.content}
            ]
        )
        initial_message = initial_response["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error generating initial message: {e}")
        initial_message = "日記について会話を開始できませんでした。"

    return render_template("chat.html", entry=entry, initial_message=initial_message)

# 日記入力フォーム
@app.route("/")
def index():
    return render_template("index.html", default_date=datetime.now().strftime("%Y-%m-%d"))

# 日記保存後に日記一覧へリダイレクト
@app.route("/save", methods=["POST"])
def save_diary():
    title = request.form.get("title")
    content = request.form.get("content")
    date = request.form.get("date")
    correction = generate_correction(content)

    new_entry = DiaryEntry(
        title=title,
        content=content,
        date=date,
        correction=correction
    )
    db.session.add(new_entry)
    db.session.commit()
    # 日記一覧ページにリダイレクト
    return redirect("/entries")

# 日記一覧表示
@app.route("/entries")
def show_entries():
    entries = DiaryEntry.query.all()
    return render_template("entries.html", entries=entries)

# 日記削除
@app.route("/delete/<int:entry_id>", methods=["POST"])
def delete_entry(entry_id):
    entry = DiaryEntry.query.get(entry_id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return redirect("/entries")

# GPTの添削生成
def generate_correction(content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは優秀な日本語教師です。以下の文章を添削してください。"},
                {"role": "user", "content": content}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error generating correction: {e}")
        return "添削を生成できませんでした。"

if __name__ == "__main__":
    app.run(debug=True)
