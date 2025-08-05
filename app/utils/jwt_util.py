import os
import jwt
import logging
import datetime
from app.models.user_model import User
from fastapi import Request, HTTPException


SECRET_KEY = os.getenv('SECRET_KEY')

def encode_auth_token(fin_kod, role, approved):
    try:
        expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

        payload = {
            'fin_kod': fin_kod,
            'role': role,
            'approved': approved,
            'exp': expiration_time
        }

        auth_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return auth_token

    except Exception as e:
        logging.getLogger(__name__).error(f"Error encoding token: {e}")
        return str(e)


def decode_auth_token(auth_token):
    try:
        logging.getLogger(__name__).debug(f"Decoding token: {auth_token}")

        payload = jwt.decode(auth_token, SECRET_KEY, algorithms=['HS256'], options={"require": ["exp"]})

        logging.getLogger(__name__).debug(f"Decoded payload: {payload}")

        return {
            'user_id': payload['sub'],
            'role': payload['role'],
            'approved': payload['approved'],
            'is_frozen': payload['is_frozen']
        }

    except jwt.ExpiredSignatureError:
        logging.getLogger(__name__).warning("Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logging.getLogger(__name__).warning(f"Invalid token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logging.getLogger(__name__).error(f"Error decoding token: {e}")
        raise HTTPException(status_code=500, detail="Error decoding token")