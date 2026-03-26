from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, os, re
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DB_ID = os.environ.get("NOTION_DB_ID", "19e7f080962180fc8d78ee6d7ad75c6c")


def format_phone(phone):
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11 and digits.startswith('010'):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    elif len(digits) == 10 and digits.startswith('02'):
        return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
    return phone


def get_next_no():
    try:
        res = requests.post(
            f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query",
            headers={
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            },
            json={
                "sorts": [{"property": "NO.", "direction": "descending"}],
                "page_size": 1
            }
        )
        if res.ok:
            results = res.json().get("results", [])
            if results:
                no_prop = results[0].get("properties", {}).get("NO.", {})
                rich_text = no_prop.get("rich_text", [])
                if rich_text:
                    current_no = rich_text[0].get("text", {}).get("content", "0000")
                    return str(int(current_no) + 1).zfill(4)
        return "0455"
    except Exception:
        return "0455"


@app.route("/api/consult", methods=["POST", "OPTIONS"])
def consult():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200
    try:
        data = request.json
        name    = data.get("name", "미입력")
        phone   = format_phone(data.get("phone", ""))
        type_   = data.get("type", "")
        message = data.get("message", "")
        today   = datetime.now().strftime("%Y-%m-%d")
        next_no = get_next_no()

        body = {
            "parent": {"database_id": NOTION_DB_ID},
            "properties": {
                "손님이름": {"title": [{"text": {"content": name}}]},
                "연락처":   {"phone_number": phone},
                "NO.":      {"rich_text": [{"text": {"content": next_no}}]},
                "특이사항": {"rich_text": [{"text": {"content": f"[{type_}] {message}" if type_ else message}}]},
                "문의날짜": {"date": {"start": today}},
                "진행상황": {"select": {"name": "홈페이지문의"}},
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
            print(f"Notion API Error: {res.status_code} - {res.text}")
            return jsonify({"success": False, "error": res.text, "status": res.status_code}), 500
    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
