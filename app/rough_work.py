# # # import cloudinary
# # # import cloudinary.uploader
# # # from cloudinary.utils import cloudinary_url

# # # Configuration       
# # cloudinary.config( 
# #     cloud_name = "dclelz8ds", 
# #     api_key = "755836139361584", 
# #     api_secret = "Ki5JoMVlEUVjxfZr0EJj4JvOy3A", # Click 'View API Keys' above to copy your API secret
# #     secure=True
# # )


# # response = cloudinary.uploader.upload(
# #     "C:/p_k workplace/backend/img1.jpg",
# #     folder="PartyKart",  # Target folder in Cloudinary
# #     use_filename=True,   # Keep original filename
# #     unique_filename=False  # Don't auto-generate random names
# # )

# # print("URL:", response["secure_url"])

# def generate_password_from_number(phone_number: str) -> str:
#     if not phone_number.isdigit() or len(phone_number) != 10:
#         raise ValueError("Phone number must be a 10-digit number")

#     first_part = phone_number[:5]
#     second_part = phone_number[5:]
#     password = f"pass{first_part}word{second_part}"
#     return password


# print(generate_password_from_number("1234567890"))  # Output: pass12345word67890



# import asyncio
# from app.microservices.common_function import send_templated_email

# order_template = """
# <h2>Hello {{ name }},</h2>
# <p>Thanks for your order! 🎉</p>
# <p>Your order ID is <b>{{ order_id }}</b>.</p>
# <p>We'll notify you once it ships.</p>
# """

# async def send_email():
#     result = await send_templated_email(
#         to_email="sandeshmorea.c.patil@gmail.com",
#         subject="Your Order Confirmation",
#         template_str=order_template,
#         context={"name": "Sandesh", "order_id": "PK-12345"},
#     )
#     print("✅ Email sent successfully")

# # ✅ Note the parentheses here ↓
# asyncio.run(send_email())



import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_test_email(from_email: str, app_password: str, to_email: str):
    """
    Send a test email using Gmail SMTP.

    Args:
        from_email: Your Gmail address (e.g. 'thepartykart.service@gmail.com')
        app_password: Your 16-character Gmail App Password
        to_email: Recipient email address
    """
    try:
        # 1️⃣ Create SMTP connection
        print("🔄 Connecting to Gmail SMTP server...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        # 2️⃣ Login
        server.login(from_email, app_password)
        print("✅ Logged in successfully.")

        # 3️⃣ Create the email
        subject = "✅ Test Email from FastAPI SMTP Setup"
        body = """
        <h2>Hello from ThePartyKart 🎉</h2>
        <p>This is a <b>test email</b> sent using Gmail SMTP and App Password.</p>
        <p>If you're reading this, your setup is working perfectly! 🚀</p>
        """

        msg = MIMEMultipart("alternative")
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        # 4️⃣ Send email
        server.sendmail(from_email, to_email, msg.as_string())
        print(f"📩 Email successfully sent to {to_email}")

        # 5️⃣ Close connection
        server.quit()
        print("🔒 Connection closed.")

    except smtplib.SMTPAuthenticationError:
        print("❌ AUTH ERROR: Gmail rejected the username or app password.")
    except Exception as e:
        print("⚠️ ERROR:", e)


# 🔹 Example usage
if __name__ == "__main__":
    send_test_email(
        from_email="thepartykart.service@gmail.com",
        app_password="tpjynacphveleaek",   # <-- Your App Password
        to_email="sandeshmorea.c.patil@gmail.com",  # <-- Send to your own email
    )
