from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import bcrypt

# Workaround: passlib<=1.7.4 tries to read bcrypt.__about__.__version__,
# which was removed in bcrypt>=4.0. This triggers a caught exception that
# still prints a noisy traceback. Provide a compatible attribute to silence it.
try:
    _ = bcrypt.__about__.__version__  # type: ignore[attr-defined]
except Exception:
    class _About:  # minimal shim for passlib expectation
        __version__ = getattr(bcrypt, "__version__", "0")
    bcrypt.__about__ = _About()  # type: ignore[attr-defined]

# Secret key to encode JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to hash password
def get_password_hash(password):
    return pwd_context.hash(password)

# Function to create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
