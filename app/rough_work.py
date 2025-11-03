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



