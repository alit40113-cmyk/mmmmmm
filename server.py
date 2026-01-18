from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# تحكم بسيط بالسرعة لكل License
LAST_CALL = {}
MIN_INTERVAL = 2  # ثانيتين بين كل طلب (تقدر تغيرها)

@app.route("/")
def home():
    return "Username Check Server Running"

@app.route("/check_username", methods=["POST"])
def check_username():
    data = request.get_json(force=True)

    username = data.get("username")
    license_key = data.get("license_key")

    if not username or not license_key:
        return jsonify({"status": "error", "reason": "bad_request"}), 400

    # rate limit بسيط
    now = time.time()
    last = LAST_CALL.get(license_key, 0)
    if now - last < MIN_INTERVAL:
        return jsonify({
            "status": "rate_limited",
            "retry_after": MIN_INTERVAL
        }), 200

    LAST_CALL[license_key] = now

    # =========================
    # منطق الفحص (مؤقت / نظيف)
    # =========================
    # هذا مكان الفحص الحقيقي لاحقاً
    # حالياً مثال فقط
    if len(username) < 5:
        return jsonify({"status": "taken"})
    elif username.endswith("x"):
        return jsonify({"status": "available"})
    else:
        return jsonify({"status": "unknown"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
