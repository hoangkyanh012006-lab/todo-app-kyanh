import streamlit as st
import requests
import pyrebase
import re
import streamlit.components.v1 as components

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="ToDo - Quản lý Công Việc", page_icon="📌", layout="centered")

st.markdown("""
    <style>
    .task-card { border: 1px solid #e6e9ef; padding: 15px; border-radius: 10px; margin-bottom: 15px; background-color: #ffffff; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# Link Backend (Lưu ý: Localhost chỉ chạy được khi bạn bật server FastAPI ở máy)
BACKEND_URL = "http://127.0.0.1:8000"

# --- 2. XỬ LÝ TOKEN TỪ URL (GOOGLE AUTH) ---
if "token" in st.query_params:
    st.session_state['userToken'] = st.query_params["token"]
    st.query_params.clear()
    st.rerun()

# --- 3. CẤU HÌNH FIREBASE ---
firebaseConfig = {
    "apiKey": "AIzaSyC0a_5qhZYUW5msHxBjnmoFZKAtkQVuhaA",
    "authDomain": "todo-app-7971d.firebaseapp.com",
    "projectId": "todo-app-7971d",
    "databaseURL": "https://todo-app-7971d-default-rtdb.firebaseio.com",
    "storageBucket": "todo-app-7971d.appspot.com"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

if 'userToken' not in st.session_state:
    st.session_state['userToken'] = None

st.title("📌 ToDo - Quản lý & Chia sẻ")

def check_password_strength(password):
    if len(password) < 6: return False
    if not re.search(r"[A-Z]", password): return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): return False
    return True

# ==========================================
# GIAO DIỆN KHI CHƯA ĐĂNG NHẬP
# ==========================================
if st.session_state['userToken'] is None:
    tab1, tab2, tab3 = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký", "🌐 Đăng nhập Google"])

    with tab1:
        email_login = st.text_input("Email đăng nhập:", key="l_email")
        pass_login = st.text_input("Mật khẩu:", type="password", key="l_pass")
        if st.button("Đăng nhập", type="primary", key="l_btn"):
            try:
                user = auth.sign_in_with_email_and_password(email_login, pass_login)
                st.session_state['userToken'] = user['idToken']
                st.rerun()
            except:
                st.error("Sai Email hoặc Mật khẩu!")

    with tab2:
        email_reg = st.text_input("Email đăng ký mới:", key="r_email")
        pass_reg = st.text_input("Tạo mật khẩu:", type="password", key="r_pass")
        st.caption("⚠️ *Mật khẩu từ 6 ký tự, gồm 1 chữ HOA và 1 ký tự đặc biệt.*")
        if st.button("Đăng ký ngay", type="primary", key="r_btn"):
            if not check_password_strength(pass_reg):
                st.error("❌ Mật khẩu chưa đủ mạnh!")
            else:
                try:
                    auth.create_user_with_email_and_password(email_reg, pass_reg)
                    st.success("✅ Đăng ký thành công! Hãy quay lại tab Đăng nhập.")
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    with tab3:
        st.info("Nhấp vào nút dưới đây để xác thực qua tài khoản Google.")
        
        google_login_html = f"""
        <html>
            <head>
                <style>
                    .g-btn {{
                        background-color: #ffffff; color: #757575; padding: 12px;
                        border: 1px solid #ddd; border-radius: 5px; cursor: pointer;
                        font-family: 'Roboto', sans-serif; font-size: 15px; width: 100%;
                        font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,.25);
                        display: flex; align-items: center; justify-content: center;
                    }}
                    .g-btn:hover {{ background-color: #f8f8f8; }}
                </style>
            </head>
            <body>
                <button id="gbtn" class="g-btn">
                    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" style="width:20px; margin-right:10px;"/>
                    Tiếp tục với Google
                </button>
                <script type="module">
                    import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
                    import {{ getAuth, signInWithPopup, GoogleAuthProvider }} from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";
                    
                    const firebaseConfig = {{
                        apiKey: "{firebaseConfig['apiKey']}",
                        authDomain: "{firebaseConfig['authDomain']}",
                        projectId: "{firebaseConfig['projectId']}"
                    }};
                    
                    const app = initializeApp(firebaseConfig);
                    const auth = getAuth(app); // Sử dụng 'auth', tuyệt đối không dùng 'fireauth'
                    const provider = new GoogleAuthProvider();

                    document.getElementById('gbtn').addEventListener('click', () => {{
                        signInWithPopup(auth, provider).then((result) => {{
                            result.user.getIdToken().then((token) => {{
                                const currentUrl = new URL(window.parent.location.href);
                                currentUrl.searchParams.set("token", token);
                                window.parent.location.href = currentUrl.toString();
                            }});
                        }}).catch((error) => {{
                            alert("Lỗi Firebase: " + error.message);
                        }});
                    }});
                </script>
            </body>
        </html>
        """
        components.html(google_login_html, height=100)

# ==========================================
# GIAO DIỆN KHI ĐÃ ĐĂNG NHẬP
# ==========================================
else:
    token = st.session_state['userToken']
    headers = {"Authorization": f"Bearer {token}"}

    col_title, col_logout = st.columns([0.8, 0.2])
    with col_logout:
        if st.button("Đăng xuất"):
            st.session_state['userToken'] = None
            st.rerun()

    with st.expander("➕ Thêm công việc mới"):
        t_title = st.text_input("Tên công việc:")
        t_notes = st.text_area("Ghi chú:")
        if st.button("Lưu", type="primary"):
            requests.post(f"{BACKEND_URL}/todos/",
                          json={"title": t_title, "completed": False, "notes": t_notes, "subtasks": [], "shared_with": []},
                          headers=headers)
            st.rerun()

    st.divider()

    c_search, c_filter = st.columns([0.6, 0.4])
    search_q = c_search.text_input("🔍 Tìm kiếm:")
    f_status = c_filter.selectbox("🏷️ Trạng thái:", ["Tất cả", "Chưa xong", "Đã xong"])

    try:
        response = requests.get(f"{BACKEND_URL}/todos/", headers=headers)
        if response.status_code == 200:
            todos = response.json().get("todos", [])
            
            # Phân loại ToDo
            my_tasks = [t for t in todos if not t.get('is_shared') and len(t.get('shared_with', [])) == 0]
            shared_me = [t for t in todos if t.get('is_shared')]
            shared_others = [t for t in todos if len(t.get('shared_with', [])) > 0 and not t.get('is_shared')]

            def render_list(task_list, is_owner=True):
                if not task_list:
                    st.info("Danh sách trống.")
                    return
                for todo in task_list:
                    # Bộ lọc UI
                    if f_status == "Đã xong" and not todo['completed']: continue
                    if f_status == "Chưa xong" and todo['completed']: continue
                    if search_q.lower() not in todo['title'].lower(): continue

                    st.markdown('<div class="task-card">', unsafe_allow_html=True)
                    c_n, c_s = st.columns([0.7, 0.3])
                    with c_n:
                        if not is_owner: st.warning(f"🤝 **[{todo.get('owner_email')}]** {todo['title']}")
                        elif len(todo.get('shared_with', [])) > 0: st.success(f"📤 **[Đã chia sẻ]** {todo['title']}")
                        else: st.info(f"📝 {todo['title']}")
                    with c_s:
                        st.write("🟢 Xong" if todo['completed'] else "🔴 Chưa")
                    
                    with st.expander("Thao tác"):
                        if todo.get('notes'): st.write(f"*{todo['notes']}*")
                        btn_c1, btn_c2 = st.columns(2)
                        if btn_c1.button("Đổi trạng thái", key=f"st_{todo['id']}"):
                            requests.put(f"{BACKEND_URL}/todos/{todo['id']}?completed={not todo['completed']}", headers=headers)
                            st.rerun()
                        if is_owner:
                            if btn_c2.button("Xóa", key=f"del_{todo['id']}"):
                                requests.delete(f"{BACKEND_URL}/todos/{todo['id']}", headers=headers)
                                st.rerun()
                            st.write("---")
                            mail = st.text_input("Chia sẻ đến (Email):", key=f"m_{todo['id']}")
                            if st.button("Chia sẻ", key=f"sh_{todo['id']}"):
                                requests.post(f"{BACKEND_URL}/todos/{todo['id']}/share", json={"email": mail}, headers=headers)
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            t1, t2, t3 = st.tabs(["Việc của tôi", "Được chia sẻ", "Đã chia sẻ"])
            with t1: render_list(my_tasks)
            with t2: render_list(shared_me, is_owner=False)
            with t3: render_list(shared_others)
    except:
        st.warning("⚠️ Không kết nối được Backend. Vui lòng bật server FastAPI!")
