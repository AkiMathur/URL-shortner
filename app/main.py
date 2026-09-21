import bcrypt

passw = b"123A"

salt = bcrypt.gensalt()

hashed = bcrypt.hashpw(password=passw, salt=salt)
print(hashed)
print(hashed.decode('utf-8'))