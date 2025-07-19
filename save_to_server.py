from flask import Flask, request, jsonify
import os, json, base64
import threading
import analyzer  

# 📁 Абсолютный путь к папке /date рядом с этим скриптом
BASE_DIR = os.path.join(os.path.dirname(__file__), "date")

app = Flask(__name__)

app.static_folder = BASE_DIR 

def ensure_dir(path):
	os.makedirs(path, exist_ok=True)

def save_file(base64_data, path):
	ensure_dir(os.path.dirname(path))
	with open(path, "wb") as f:
		f.write(base64.b64decode(base64_data.split(",")[-1]))

@app.route("/save_profile", methods=["POST"])
def save_profile():
	try:
		data = request.json
		profile_type = data.get("profile_type")   # "my", "partner", "dialog"
		profile_name = data.get("profile_name")   # Имя из UI

		if profile_type not in ["my", "partner", "dialog"]:
			return jsonify({"status": "error", "message": "Invalid profile type"}), 400
		if not profile_name:
			return jsonify({"status": "error", "message": "Profile name is missing"}), 400

		# 🗂 Путь к папке профиля
		session_id = data.get("session_id", "global")
		profile_root = os.path.join(BASE_DIR, session_id, profile_type, profile_name)
		ensure_dir(profile_root)

		# 💁‍♂️ МОЙ ПРОФИЛЬ
		if profile_type == "my":
			for i, img in enumerate(data.get("photos", [])):
				save_file(img, os.path.join(profile_root, "photos", f"photo{i}.jpg"))

			for i, img in enumerate(data.get("description", [])):
				save_file(img, os.path.join(profile_root, "description", f"desc{i}.jpg"))

			if data.get("analysis"):
				ensure_dir(os.path.join(profile_root, "analysis"))
				with open(os.path.join(profile_root, "analysis", "analysis.json"), "w", encoding="utf-8") as f:
					json.dump(data["analysis"], f, ensure_ascii=False, indent=2)

		# 👤 ЧУЖОЙ ПРОФИЛЬ
		elif profile_type == "partner":
			for i, img in enumerate(data.get("photos", [])):
				save_file(img, os.path.join(profile_root, "photos", f"photo{i}.jpg"))

			if data.get("analysis"):
				ensure_dir(os.path.join(profile_root, "analysis"))
				with open(os.path.join(profile_root, "analysis", "analysis.json"), "w", encoding="utf-8") as f:
					json.dump(data["analysis"], f, ensure_ascii=False, indent=2)

		# 💬 ДИАЛОГ
		elif profile_type == "dialog":
			for i, img in enumerate(data.get("screenshots", [])):
				save_file(img, os.path.join(profile_root, "screenshots", f"dialog{i}.jpg"))

			if data.get("analysis"):
				ensure_dir(os.path.join(profile_root, "analysis"))
				with open(os.path.join(profile_root, "analysis", "analysis.json"), "w", encoding="utf-8") as f:
					json.dump(data["analysis"], f, ensure_ascii=False, indent=2)

		print(f"[✔] Сохранено: {profile_type}/{profile_name}")
		return jsonify({"status": "ok", "profile": profile_name, "type": profile_type})

	except Exception as e:
		import traceback
		traceback.print_exc()
		return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/list_profiles", methods=["GET", "POST"])
def list_profiles():
	from glob import glob

	result = {
		"my": [],
		"partner": []
	}
	session_id = request.json.get("session_id", "global")
	for typ in ["my", "partner"]:
		dir_path = os.path.join(BASE_DIR, session_id, typ)
		if os.path.exists(dir_path):
			result[typ] = [
				name for name in os.listdir(dir_path)
				if os.path.isdir(os.path.join(dir_path, name))
			]
	return jsonify(result)

@app.route("/get_profile", methods=["POST"])
def get_profile():
	try:
		data = request.json
		profile_type = data.get("profile_type")
		profile_name = data.get("profile_name")
		
		session_id = data.get("session_id", "global")
		base_path = os.path.join(BASE_DIR, session_id, profile_type, profile_name)
		result = {}

		# Фото
		photos_dir = os.path.join(base_path, "photos")
		if os.path.exists(photos_dir):
			result["photos"] = [
				"/".join(["static", profile_type, profile_name, "photos", f])
				for f in os.listdir(photos_dir)
			]

		# Описание (только для my)
		if profile_type == "my":
			desc_dir = os.path.join(base_path, "description")
			if os.path.exists(desc_dir):
				result["description"] = [
					"/".join(["static", profile_type, profile_name, "description", f])
					for f in os.listdir(desc_dir)
				]

		# Анализ
		analysis_file = os.path.join(base_path, "analysis", "analysis.json")
		if os.path.exists(analysis_file):
			with open(analysis_file, encoding="utf-8") as f:
				result["analysis"] = json.load(f)

		return jsonify(result)
	except Exception as e:
		return jsonify({"error": str(e)}), 500

@app.route("/analyze_profile", methods=["POST"])
def analyze_profile():
	try:
		data = request.json
		profile_type = data.get("profile_type")  # "my", "partner", "dialog"
		profile_name = data.get("profile_name")
		session_id = data.get("session_id", "global")
		base_path = os.path.join(BASE_DIR, session_id, profile_type, profile_name)

		if profile_type == "my":
			photo_dir = os.path.join(base_path, "photos")
			desc_dir = os.path.join(base_path, "description")

			photo_paths = [os.path.join(photo_dir, f) for f in os.listdir(photo_dir) if f.endswith(('.jpg', '.png'))]
			desc_paths = [os.path.join(desc_dir, f) for f in os.listdir(desc_dir) if f.endswith(('.jpg', '.png'))]
			desc_path = desc_paths[0] if desc_paths else None

			photo_result = analyzer.analyze_multiple_photos(photo_paths) if photo_paths else []
			desc_result = analyzer.analyze_profile_image(desc_path) if desc_path else {"text": "Описание не найдено."}

			result = {
				"photo_advice": analyzer.print_photo_analysis_results(photo_result),
				"description_advice": desc_result["text"]
			}

		elif profile_type == "partner":
			photo_dir = os.path.join(base_path, "photos")
			photo_paths = [os.path.join(photo_dir, f) for f in os.listdir(photo_dir) if f.endswith(('.jpg', '.png'))]
			desc_path = photo_paths[0] if photo_paths else None
			desc_result = analyzer.analyze_profile_image(desc_path) if desc_path else {"text": "Нет описания."}

			result = {
				"interest_advice": desc_result["text"]
			}

		elif profile_type == "dialog":
			screen_dir = os.path.join(base_path, "screenshots")
			screen_paths = [os.path.join(screen_dir, f) for f in os.listdir(screen_dir) if f.endswith(('.jpg', '.png'))]
			screenshot = screen_paths[0] if screen_paths else None
			dialog_result = analyzer.analyze_conversation_image(screenshot) if screenshot else {"analysis": "Нет скринов."}

			result = {
				"dialog_advice": dialog_result["analysis"]
			}

		else:
			return jsonify({"error": "Неверный тип профиля"}), 400

		save_path = os.path.join(base_path, "analysis", "analysis.json")
		ensure_dir(os.path.dirname(save_path))
		with open(save_path, "w", encoding="utf-8") as f:
			json.dump(result, f, ensure_ascii=False, indent=2)

		return jsonify({"status": "ok"})
	except Exception as e:
		import traceback; traceback.print_exc()
		return jsonify({"error": str(e)}), 500
		
# 🚀 Запуск сервера
if __name__ == "__main__":
	print(f"[i] BASE_DIR = {BASE_DIR}")
	app.run(host='127.0.0.1', port=5000, debug=True)
