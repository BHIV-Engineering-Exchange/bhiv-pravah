import streamlit as st
import requests
import io
import base64
import os

def show_2fa_setup():
    """2FA Setup component for Streamlit"""
    st.subheader("🔐 Two-Factor Authentication Setup")
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "demo_user"
    
    user_id = st.text_input("User ID", value=st.session_state.user_id)
    
    if st.button("🔑 Setup 2FA"):
        try:
            # Call Gateway auth endpoint
            api_base = os.getenv("GATEWAY_URL")
            if not api_base:
                st.error("❌ GATEWAY_URL environment variable not configured")
                return
            
            api_key = os.getenv("API_KEY_SECRET")
            if not api_key:
                st.error("❌ API_KEY_SECRET environment variable not configured")
                return
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{api_base}/auth/2fa/setup",
                json={"user_id": user_id},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                st.success("✅ 2FA Setup Successful!")
                
                # Display QR code
                qr_code_data = data.get("qr_code", "")
                if qr_code_data:
                    try:
                        import qrcode
                        from PIL import Image
                        # Decode base64 QR code
                        qr_data = qr_code_data.split(",")[1]  # Remove data:image/png;base64,
                        qr_bytes = base64.b64decode(qr_data)
                        qr_image = Image.open(io.BytesIO(qr_bytes))
                    except ImportError:
                        st.error("❌ QR code libraries not available")
                        return
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.image(qr_image, caption="Scan with Authenticator App")
                    
                    with col2:
                        st.write("**Manual Entry Key:**")
                        st.code(data.get("manual_entry_key", ""))
                        st.write("**Instructions:**")
                        st.info(data.get("instructions", ""))
                
                # Verification section
                st.subheader("🔍 Verify Setup")
                totp_code = st.text_input("Enter 6-digit code from your app:")
                
                if st.button("✅ Verify Code"):
                    verify_response = requests.post(
                        f"{api_base}/auth/2fa/verify",
                        json={"user_id": user_id, "totp_code": totp_code},
                        headers=headers
                    )
                    
                    if verify_response.status_code == 200:
                        st.success("🎉 2FA Verification Successful!")
                        st.balloons()
                    else:
                        st.error("❌ Invalid code. Please try again.")
            else:
                st.error(f"❌ Setup failed: {response.text}")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

def show_2fa_login():
    """2FA Login component"""
    st.subheader("🔐 Login with 2FA")
    
    with st.form("2fa_login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        totp_code = st.text_input("2FA Code (optional)")
        
        submitted = st.form_submit_button("🚀 Login")
        
        if submitted and username and password:
            try:
                api_base = os.getenv("GATEWAY_URL")
                if not api_base:
                    st.error("❌ GATEWAY_URL environment variable not configured")
                    return
                
                response = requests.post(
                    f"{api_base}/auth/login",
                    json={
                        "username": username,
                        "password": password,
                        "totp_code": totp_code if totp_code else None
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Login Successful!")
                    
                    # Store token in session
                    st.session_state.access_token = data.get("access_token")
                    st.session_state.user_id = data.get("user_id")
                    st.session_state.logged_in = True
                    
                    st.info(f"Welcome {data.get('user_id')}!")
                    if data.get("2fa_verified"):
                        st.success("🔐 2FA Verified")
                    
                    st.rerun()
                else:
                    st.error("❌ Login failed. Check credentials.")
                    
            except Exception as e:
                st.error(f"❌ Login error: {str(e)}")

if __name__ == "__main__":
    # Demo usage
    tab1, tab2 = st.tabs(["Setup 2FA", "Login with 2FA"])
    
    with tab1:
        show_2fa_setup()
    
    with tab2:
        show_2fa_login()
