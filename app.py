from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, os
from datetime import datetime

app = Flask(__name__)
CORS(app, origins="*", methods=["GET", "POST", "OPTIONS"])

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DB_ID = "19e7f080-9621-8088-aaf5-000bd030c10c"

@app.route("/api/consult", methods=["POST", "OPTIONS"])
def consult():
    data = request.json
    name    = data.get("name", "미입력")
    phone   = data.get("phone", "")
    type_   = data.get("type", "")
    message = data.get("message", "")
    today   = datetime.now().strftime("%Y-%m-%d")

    body = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": {
            "손님이름": {"title": [{"text": {"content": name}}]},
            "연락처":   {"phone_number": phone},
            "특이사항": {"rich_text": [{"text": {"content": f"[{type_}] {message}" if type_ else message}}]},
            "문의날짜": {"date": {"start": today}},
            "진행상황": {"select": {"name": "문의-쁘띠린📲"}},
            "광고물건": {"rich_text": [{"text": {"content": "쁘띠린 랜딩페이지 문의"}}]}
        }
    }

    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        },
        json=body
    )

    if res.ok:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "error": res.text}), 500

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
