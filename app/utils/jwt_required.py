from app.utils.jwt_util import decode_auth_token
from fastapi import Request, HTTPException, Depends

def token_required(allowed_roles=None):
    async def dependency(request: Request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise HTTPException(status_code=401, detail='Authorization token is missing.')

        try:
            token = auth_header.split(" ")[1]
            payload = decode_auth_token(token)

            if payload is None:
                raise HTTPException(status_code=403, detail='Token is invalid or expired.')

            if allowed_roles and payload.get('role') not in allowed_roles:
                raise HTTPException(status_code=403, detail='Access denied: role not allowed.')

            # Optionally attach user info to request.state
            request.state.user = payload
            return payload

        except IndexError:
            raise HTTPException(status_code=403, detail='Invalid token format.')
        except Exception as e:
            raise HTTPException(status_code=403, detail=f'Invalid token: {str(e)}')

    return Depends(dependency)