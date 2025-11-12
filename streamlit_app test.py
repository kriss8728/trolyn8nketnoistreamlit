import streamlit as st
import requests
import uuid
import re

# Hàm đọc nội dung từ file văn bản
def rfile(name_file):
    try:
        with open(name_file, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
            st.error(f"File {name_file} không tồn tại.")

# Constants
BEARER_TOKEN = st.secrets.get("BEARER_TOKEN")
WEBHOOK_URL = st.secrets.get("WEBHOOK_URL")

def generate_session_id():
    return str(uuid.uuid4())


    }
    
    try:
        # Debug: In ra thông tin request
        st.write("🔍 Debug Info:")
        st.write(f"- URL: {WEBHOOK_URL}")
        st.write(f"- Token exists: {bool(BEARER_TOKEN)}")
        st.write(f"- Session ID: {session_id[:8]}...")
        st.write(f"- Message: {message[:50]}...")
        
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=30)
        
        # Debug: In ra status code và response
        st.write(f"- Status Code: {response.status_code}")
        st.write(f"- Response Length: {len(response.text)} chars")
        st.write(f"- Response Headers: {dict(response.headers)}")
        st.write(f"- First 500 chars: {response.text[:500]}")
        
        # Kiểm tra status code trước
        if response.status_code != 200:
            return f"Error: Server returned status code {response.status_code}. Response: {response.text[:200]}", None
        
        # Kiểm tra nếu response trống
        if not response.text:
            return "Error: Received empty response from server", None
        
        # Thử parse JSON
        try:
            response_data = response.json()
        except ValueError as json_err:
            return f"Error: Invalid JSON response. First 200 chars: {response.text[:200]}", None
        
        # Xử lý response data
        try:
            # Trường hợp response là dictionary
            if isinstance(response_data, dict):
                content = response_data.get("content") or response_data.get("output")
                image_url = response_data.get('url', None)
            # Trường hợp response là list
            elif isinstance(response_data, list) and len(response_data) > 0:
                content = response_data[0].get("content") or response_data[0].get("output")
                image_url = response_data[0].get('url', None)
            else:
                return f"Error: Unexpected response format: {str(response_data)[:200]}", None
            
            # Kiểm tra nếu không có content
            if not content:
                return f"Error: No content found in response. Response structure: {str(response_data)[:200]}", None
                
            return content, image_url
            
        except (KeyError, IndexError, AttributeError) as e:
            return f"Error: Failed to extract content from response - {str(e)}. Response: {str(response_data)[:200]}", None
            
    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try again.", None
    except requests.exceptions.ConnectionError:
        return "Error: Failed to connect to the server. Please check your internet connection.", None
    except requests.exceptions.RequestException as e:
        return f"Error: Failed to connect to the LLM - {str(e)}", None

def extract_text(output):
    """Trích xuất văn bản từ chuỗi output (loại bỏ hình ảnh)"""
    text_only = re.sub(r'!\[.*?\]\(.*?\)', '', output)
    return text_only

def display_message_with_image(text, image_url):
    """Hiển thị tin nhắn với văn bản và hình ảnh"""
    if image_url:
        st.markdown(
            f"""
            <a href="{image_url}" target="_blank">
                <img src="{image_url}" alt="Biểu đồ" style="width: 100%; height: auto; margin-bottom: 10px;">
            </a>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown(text, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Trợ lý AI", page_icon="🤖", layout="centered")
    st.markdown(
        """
        <style>
            .assistant {
                padding: 10px;
                border-radius: 10px;
                max-width: 75%;
                background: none;
                text-align: left;
                margin-bottom: 10px;
            }
            .user {
                padding: 10px;
                border-radius: 10px;
                max-width: 75%;
                background: none;
                text-align: right;
                margin-left: auto;
                margin-bottom: 10px;
            }
            .assistant::before { content: "🤖 "; font-weight: bold; }
            .user::before { content: " "; font-weight: bold; }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Hiển thị logo (nếu có)
    try:
        col1, col2, col3 = st.columns([3, 2, 3])
        with col2:
            st.image("logo.png")
    except:
        pass
    
    # Đọc nội dung tiêu đề từ file
    try:
        with open("00.xinchao.txt", "r", encoding="utf-8") as file:
            title_content = file.read()
    except Exception as e:
        title_content = "Trợ lý AI"

    st.markdown(
        f"""<h1 style="text-align: center; font-size: 24px;">{title_content}</h1>""",
        unsafe_allow_html=True
    )

    # Khởi tạo session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = generate_session_id()

    # Hiển thị lịch sử tin nhắn
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            st.markdown(f'<div class="assistant">{message["content"]}</div>', unsafe_allow_html=True)
            if "image_url" in message and message["image_url"]:
                st.markdown(
                    f"""
                    <a href="{message['image_url']}" target="_blank">
                        <img src="{message['image_url']}" alt="Biểu đồ" style="width: 100%; height: auto; margin-bottom: 10px;">
                    </a>
                    """,
                    unsafe_allow_html=True
                )
        elif message["role"] == "user":
            st.markdown(f'<div class="user">{message["content"]}</div>', unsafe_allow_html=True)

    # Ô nhập liệu cho người dùng
    if prompt := st.chat_input("Nhập nội dung cần trao đổi ở đây nhé?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.markdown(f'<div class="user">{prompt}</div>', unsafe_allow_html=True)
        
        with st.spinner("Đang chờ phản hồi từ AI..."):
            llm_response, image_url = send_message_to_llm(st.session_state.session_id, prompt)
    
        if isinstance(llm_response, str) and "Error" in llm_response:
            st.error(llm_response)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": llm_response,
                "image_url": None
            })
        else:
            st.markdown(f'<div class="assistant">{llm_response}</div>', unsafe_allow_html=True)
            
            if image_url:
                st.markdown(
                    f"""
                    <a href="{image_url}" target="_blank">
                        <img src="{image_url}" alt="Biểu đồ" style="width: 100%; height: auto; margin-bottom: 10px;">
                    </a>
                    """,
                    unsafe_allow_html=True
                )
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": llm_response,
                "image_url": image_url
            })
        
        st.rerun()

if __name__ == "__main__":
    main()