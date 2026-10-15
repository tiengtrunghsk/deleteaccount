import os
import json
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, auth, firestore

# Khởi tạo Firebase Admin SDK
firebase_json_str = os.environ.get("FIREBASE_CREDENTIALS_JSON")

if firebase_json_str:
    cred_dict = json.loads(firebase_json_str)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
else:
    if os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    else:
        raise ValueError("Chưa cấu hình thông tin xác thực Firebase cho Admin SDK!")

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "running", "message": "Firebase Admin API đang hoạt động!"})

@app.route('/api/delete-user', methods=['POST'])
def delete_user():
    data = request.json or {}
    email = data.get('email')
    
    if not email:
        return jsonify({"success": False, "error": "Thiếu thông tin email"}), 400
        
    email_clean = email.strip().lower()
    
    try:
        db = firestore.client()
        deleted_auth = False
        deleted_firestore = False
        
        # 1. Xóa tài khoản trong Firebase Authentication
        try:
            user_record = auth.get_user_by_email(email_clean)
            auth.delete_user(user_record.uid)
            deleted_auth = True
        except firebase_admin.auth.UserNotFoundError:
            pass
            
        # 2. Xóa document trong Firestore (collection allowed_users)
        doc_ref = db.collection('allowed_users').document(email_clean)
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.delete()
            deleted_firestore = True
            
        if not deleted_auth and not deleted_firestore:
            return jsonify({"success": False, "error": f"Không tìm thấy user {email_clean} trong hệ thống."}), 404
            
        return jsonify({
            "success": True, 
            "message": f"Đã xóa hoàn toàn user {email_clean} (Auth: {deleted_auth}, Firestore: {deleted_firestore})"
        })
        
    except Exception as e:
        # In chi tiết lỗi ra terminal/log của Render để dễ dàng debug
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
