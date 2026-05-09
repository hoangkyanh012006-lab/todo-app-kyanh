import streamlit as st
import requests
import pyrebase
import re
import streamlit.components.v1 as components  # <--- CÔNG CỤ NHÚNG GIAO DIỆN

st.set_page_config(page_title="ToDo - Quản lý Công Việc", page_icon="📌", layout="centered")

st.markdown("""
    <style>
    .task-card { border: 1px solid #e6e9ef; padding: 10px; border-radius: 10px; margin-bottom: 15px; background-color: #ffffff; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

BACKEND_URL = "http://127.0.0.1:8000"

# ==========================================
# THỦ THUẬT BẮC CẦU: BẮT VÉ TỪ GOOGLE
# ==========================================
params = st.experimental_get_query_params()
if "token" in params:
    # Nếu thấy vé trên thanh URL, lập tức cất vào túi và xóa URL đi cho sạch
    st.session_state['userToken'] = params["token"][0]
    st.experimental_set_query_params()

# --- ĐIỀN API KEY CỦA EM VÀO ĐÂY ---
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
# GIAO DIỆN ĐĂNG NHẬP / ĐĂNG KÝ
# ==========================================
if st.session_state['userToken'] is None:
    # THÊM TAB SỐ 3 DÀNH CHO GOOGLE
    tab1, tab2, tab3 = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký", "🌐 Đăng nhập Google"])

    with tab1:
        email_login = st.text_input("Email đăng nhập:")
        pass_login = st.text_input("Mật khẩu:", type="password", key="pl")
        if st.button("Đăng nhập", type="primary"):
            try:
                user = auth.sign_in_with_email_and_password(email_login, pass_login)
                st.session_state['userToken'] = user['idToken']
                st.experimental_rerun()
            except Exception as e:
                st.error("Sai Email hoặc Mật khẩu!")

    with tab2:
        email_reg = st.text_input("Email đăng ký mới:")
        pass_reg = st.text_input("Tạo mật khẩu:", type="password", key="pr")
        st.caption("⚠️ *Lưu ý: Mật khẩu phải từ 6 ký tự trở lên, gồm ít nhất 1 chữ IN HOA và 1 ký tự đặc biệt.*")
        if st.button("Đăng ký ngay", type="primary"):
            if not check_password_strength(pass_reg):
                st.error("❌ Mật khẩu chưa đủ mạnh!")
            else:
                try:
                    user = auth.create_user_with_email_and_password(email_reg, pass_reg)
                    st.success("✅ Đăng ký thành công!")
                except Exception as e:
                    st.error(f"Lỗi đăng ký: {e}")

    with tab3:
        st.info("Nhấp vào nút dưới đây để mở cửa sổ xác thực của Google.")

        # ĐOẠN MÃ NHÚNG NÚT GOOGLE (Dùng HTML/Javascript)
        # ĐOẠN MÃ NHÚNG NÚT GOOGLE (Dùng HTML/Javascript)
        google_login_html = f"""
                <html>
                    <head>
                        <style>
                            .g-btn {{
                                background-color: #ffffff; color: #757575; padding: 10px 15px;
                                border: 1px solid #ddd; border-radius: 5px; cursor: pointer;
                                font-family: Roboto, sans-serif; font-size: 15px; width: 100%;
                                font-weight: bold; box-shadow: 0 2px 4px 0 rgba(0,0,0,.25);
                                display: flex; align-items: center; justify-content: center;
                            }}
                            .g-btn:hover {{ background-color: #f5f5f5; }}
                            .g-btn img {{ width: 20px; margin-right: 10px; }}
                        </style>
                    </head>
                    <body>
                        <button id="gbtn" class="g-btn">
                            <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google logo"/>
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
                            const auth = getAuth(app);
                            const provider = new GoogleAuthProvider();

                            document.getElementById('gbtn').addEventListener('click', () => {{
                                signInWithPopup(auth, provider).then((result) => {{
                                    result.user.getIdToken().then((token) => {{
                                        window.parent.location.href = "/?token=" + token;
                                    }});
                                }}).catch((error) => {{
                                    alert("Lỗi đăng nhập: " + error.message);
                                }});
                            }});
                        </script>
                    </body>
                </html>
                """
        components.html(google_login_html, height=80)
# ==========================================
# GIAO DIỆN QUẢN LÝ CÔNG VIỆC CHÍNH (Giữ nguyên như cũ)
# ==========================================
else:
    token = st.session_state['userToken']
    headers = {"Authorization": f"Bearer {token}"}

    col_empty, col_logout = st.columns([0.8, 0.2])
    if col_logout.button("Đăng xuất"):
        st.session_state['userToken'] = None
        st.experimental_rerun()

    with st.expander("➕ Thêm công việc mới"):
        title = st.text_input("Tên công việc:")
        notes = st.text_area("Ghi chú:")
        if st.button("Lưu", type="primary"):
            requests.post(f"{BACKEND_URL}/todos/",
                          json={"title": title, "completed": False, "notes": notes, "subtasks": [], "shared_with": []},
                          headers=headers)
            st.experimental_rerun()

    st.divider()

    c_search, c_filter = st.columns([0.6, 0.4])
    search_query = c_search.text_input("🔍 Tìm kiếm tên công việc:")
    filter_status = c_filter.selectbox("🏷️ Trạng thái:", ["Tất cả", "Chưa hoàn thành", "Đã hoàn thành"])

    response = requests.get(f"{BACKEND_URL}/todos/", headers=headers)
    if response.status_code == 200:
        todos = response.json().get("todos", [])

        my_private_tasks = []
        shared_with_me = []
        tasks_i_shared = []

        for t in todos:
            if filter_status == "Đã hoàn thành" and not t['completed']: continue
            if filter_status == "Chưa hoàn thành" and t['completed']: continue
            if search_query.lower() not in t['title'].lower(): continue

            if t.get('is_shared'):
                shared_with_me.append(t)
            elif len(t.get('shared_with', [])) > 0:
                tasks_i_shared.append(t)
            else:
                my_private_tasks.append(t)


        def render_task_list(task_list, is_owner_view=True):
            if not task_list:
                st.info("Trống! Không có công việc nào trong mục này.")
                return
            for todo in task_list:
                st.markdown('<div class="task-card">', unsafe_allow_html=True)
                col_name, col_status = st.columns([0.65, 0.35])
                with col_name:
                    if not is_owner_view:
                        st.warning(f"**🤝 [Từ: {todo.get('owner_email')}]** {todo['title']}")
                    elif len(todo.get('shared_with', [])) > 0:
                        st.success(f"**📤 [Đã chia sẻ]** {todo['title']}")
                    else:
                        st.info(f"**📝 {todo['title']}**")
                with col_status:
                    if todo['completed']:
                        st.success("🟢 Đã hoàn thành")
                    else:
                        st.error("🔴 Chưa hoàn thành")
                with st.expander("Chi tiết & Thao tác"):
                    if todo.get('notes'): st.markdown(f"*{todo['notes']}*")
                    if len(todo.get('shared_with', [])) > 0 and is_owner_view:
                        st.write(f"👥 Đang chia sẻ cho: **{', '.join(todo['shared_with'])}**")
                    st.write("---")
                    c1, c2 = st.columns(2)
                    btn_text = "🔄 Đánh dấu Chưa làm" if todo['completed'] else "✅ Đánh dấu Đã xong"
                    if c1.button(btn_text, key=f"up_{todo['id']}"):
                        requests.put(f"{BACKEND_URL}/todos/{todo['id']}?completed={not todo['completed']}",
                                     headers=headers)
                        st.experimental_rerun()
                    if is_owner_view:
                        if c2.button("🗑️ Xóa công việc", key=f"del_{todo['id']}"):
                            requests.delete(f"{BACKEND_URL}/todos/{todo['id']}", headers=headers)
                            st.experimental_rerun()
                        st.write("---")
                        c_mail, c_share = st.columns([0.7, 0.3])
                        share_email = c_mail.text_input("Chia sẻ cho Email:", key=f"mail_{todo['id']}")
                        if c_share.button("Chia sẻ", key=f"share_{todo['id']}"):
                            requests.post(f"{BACKEND_URL}/todos/{todo['id']}/share", json={"email": share_email},
                                          headers=headers)
                            st.experimental_rerun()
                    else:
                        c2.write("*(Bạn không có quyền xóa công việc này)*")
                st.markdown('</div>', unsafe_allow_html=True)


        t1, t2, t3 = st.tabs(["🧑‍💻 Việc của tôi", "🤝 Được chia sẻ", "📤 Đã chia sẻ"])
        with t1:
            render_task_list(my_private_tasks, is_owner_view=True)
        with t2:
            render_task_list(shared_with_me, is_owner_view=False)
        with t3:
            render_task_list(tasks_i_shared, is_owner_view=True)