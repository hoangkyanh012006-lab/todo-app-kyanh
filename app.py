import streamlit as st
import requests
import pyrebase
import re
import streamlit.components.v1 as components

# 1. Cấu hình trang và Giao diện CSS
st.set_page_config(page_title="ToDo - Quản lý Công Việc", page_icon="📌", layout="centered")

st.markdown("""
    <style>
    .task-card { border: 1px solid #e6e9ef; padding: 10px; border-radius: 10px; margin-bottom: 15px; background-color: #ffffff; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# LƯU Ý: Khi chạy trên Cloud, URL này cần được thay đổi thành link Backend thật (Render/Railway)
BACKEND_URL = "http://127.0.0.1:8000"

# 2. Xử lý Token từ Google (Bắc cầu qua URL)
if "token" in st.query_params:
    st.session_state['userToken'] = st.query_params["token"]
    # Xóa tham số trên URL để thanh địa chỉ sạch sẽ
    st.query_params.clear()
    st.rerun()

# 3. Cấu hình Firebase
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
# GIAO DIỆN CHƯA ĐĂNG NHẬP
# ==========================================
if st.session_state['userToken'] is None:
    tab1, tab2, tab3 = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký", "🌐 Đăng nhập Google"])

    with tab1:
        email_login = st.text_input("Email đăng nhập:", key="login_email")
        pass_login = st.text_input("Mật khẩu:", type="password", key="login_pass")
        if st.button("Đăng nhập", type="primary", key="btn_login"):
            try:
                user = auth.sign_in_with_email_and_password(email_login, pass_login)
                st.session_state['userToken'] = user['idToken']
                st.rerun()
            except Exception:
                st.error("Sai Email hoặc Mật khẩu!")

    with tab2:
        email_reg = st.text_input("Email đăng ký mới:", key="reg_email")
        pass_reg = st.text_input("Tạo mật khẩu:", type="password", key="reg_pass")
        st.caption("⚠️ *Mật khẩu từ 6 ký tự, gồm 1 chữ HOA và 1 ký tự đặc biệt.*")
        if st.button("Đăng ký ngay", type="primary", key="btn_reg"):
            if not check_password_strength(pass_reg):
                st.error("❌ Mật khẩu chưa đủ mạnh!")
            else:
                try:
                    auth.create_user_with_email_and_password(email_reg, pass_reg)
                    st.success("✅ Đăng ký thành công! Hãy chuyển sang tab Đăng nhập.")
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    with tab3:
        st.info("Nhấp vào nút dưới đây để xác thực qua tài khoản Google.")

        # ĐOẠN MÃ GOOGLE LOGIN (Đã sửa lỗi fireauth và origin)
        google_login_html = f"""
        <html>
            <body>
                <button id="gbtn" style="background-color: #ffffff; color: #757575; padding: 10px 15px; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; font-family: Roboto, sans-serif; font-size: 15px; width: 100%; font-weight: bold; box-shadow: 0 2px 4px 0 rgba(0,0,0,.25); display: flex; align-items: center; justify-content: center;">
                    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" style="width: 20px; margin-right: 10px;"/>
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
                                // Chuyển hướng trang cha và đính kèm token
                                const parentUrl = new URL(window.parent.location.href);
                                parentUrl.searchParams.set("token", token);
                                window.parent.location.href = parentUrl.toString();
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
# GIAO DIỆN QUẢN LÝ CÔNG VIỆC CHÍNH
# ==========================================
else:
    token = st.session_state['userToken']
    headers = {"Authorization": f"Bearer {token}"}

    col_empty, col_logout = st.columns([0.8, 0.2])
    if col_logout.button("Đăng xuất"):
        st.session_state['userToken'] = None
        st.rerun()

    with st.expander("➕ Thêm công việc mới"):
        title = st.text_input("Tên công việc:")
        notes = st.text_area("Ghi chú:")
        if st.button("Lưu", type="primary"):
            requests.post(f"{BACKEND_URL}/todos/",
                          json={"title": title, "completed": False, "notes": notes, "subtasks": [], "shared_with": []},
                          headers=headers)
            st.rerun()

    st.divider()

    c_search, c_filter = st.columns([0.6, 0.4])
    search_query = c_search.text_input("🔍 Tìm kiếm tên công việc:")
    filter_status = c_filter.selectbox("🏷️ Trạng thái:", ["Tất cả", "Chưa hoàn thành", "Đã hoàn thành"])

    # Lấy danh sách ToDo từ Backend
    try:
        response = requests.get(f"{BACKEND_URL}/todos/", headers=headers)
        if response.status_code == 200:
            todos = response.json().get("todos", [])

            # Phân loại ToDo
            my_private_tasks = [t for t in todos if not t.get('is_shared') and len(t.get('shared_with', [])) == 0]
            shared_with_me = [t for t in todos if t.get('is_shared')]
            tasks_i_shared = [t for t in todos if len(t.get('shared_with', [])) > 0 and not t.get('is_shared')]


            def render_task_list(task_list, is_owner_view=True):
                if not task_list:
                    st.info("Trống! Không có công việc nào.")
                    return
                for todo in task_list:
                    # Lọc dữ liệu theo UI
                    if filter_status == "Đã hoàn thành" and not todo['completed']: continue
                    if filter_status == "Chưa hoàn thành" and todo['completed']: continue
                    if search_query.lower() not in todo['title'].lower(): continue

                    st.markdown('<div class="task-card">', unsafe_allow_html=True)
                    col_name, col_status = st.columns([0.6, 0.4])
                    with col_name:
                        if not is_owner_view:
                            st.warning(f"🤝 **[{todo.get('owner_email')}]** {todo['title']}")
                        elif len(todo.get('shared_with', [])) > 0:
                            st.success(f"📤 **[Đã chia sẻ]** {todo['title']}")
                        else:
                            st.info(f"📝 {todo['title']}")
                    with col_status:
                        st.write("🟢 Xong" if todo['completed'] else "🔴 Chưa xong")

                    with st.expander("Chi tiết & Thao tác"):
                        if todo.get('notes'): st.markdown(f"*{todo['notes']}*")
                        c1, c2 = st.columns(2)
                        if c1.button("✅/🔄", key=f"up_{todo['id']}"):
                            requests.put(f"{BACKEND_URL}/todos/{todo['id']}?completed={not todo['completed']}",
                                         headers=headers)
                            st.rerun()
                        if is_owner_view:
                            if c2.button("🗑️ Xóa", key=f"del_{todo['id']}"):
                                requests.delete(f"{BACKEND_URL}/todos/{todo['id']}", headers=headers)
                                st.rerun()
                            st.write("---")
                            c_mail, c_share = st.columns([0.7, 0.3])
                            share_email = c_mail.text_input("Chia sẻ tới Email:", key=f"mail_{todo['id']}")
                            if c_share.button("Gửi", key=f"share_{todo['id']}"):
                                requests.post(f"{BACKEND_URL}/todos/{todo['id']}/share", json={"email": share_email},
                                              headers=headers)
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)


            t1, t2, t3 = st.tabs(["🧑‍💻 Việc của tôi", "🤝 Được chia sẻ", "📤 Đã chia sẻ"])
            with t1:
                render_task_list(my_private_tasks)
            with t2:
                render_task_list(shared_with_me, is_owner_view=False)
            with t3:
                render_task_list(tasks_i_shared)
    except Exception as e:
        st.error(f"Không thể kết nối Backend tại {BACKEND_URL}. Hãy đảm bảo Backend đang chạy!")
