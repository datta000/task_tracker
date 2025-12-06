from functools import wraps
from flask import request, jsonify, current_app, g
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

def extract_token_from_header():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header:
        return None, jsonify({"error": "Missing Authorization header"}), 401

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None, jsonify({"error": "Malformed Authorization header"}), 401

    return parts[1], None, None

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token, resp, status = extract_token_from_header()
        if resp:
            return resp, status

        secret = current_app.config.get('SECRET_KEY')
        if not secret:
            return jsonify({"error": "Server misconfiguration"}), 500

        try:
            decoded = jwt.decode(token, secret, algorithms=["HS256"])
            # Attach user info to flask.g
            g.user = decoded
        except ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"error": str(e)}), 401

        return f(*args, **kwargs)
    return wrapper

def role_required(required_role):
    """
    Decorator that requires login and a specific role in token payload.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # reuse login_required logic
            token, resp, status = extract_token_from_header()
            if resp:
                return resp, status

            secret = current_app.config.get('SECRET_KEY')
            if not secret:
                return jsonify({"error": "Server misconfiguration"}), 500

            try:
                decoded = jwt.decode(token, secret, algorithms=["HS256"])
            except ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401
            except Exception as e:
                return jsonify({"error": str(e)}), 401

            if decoded.get("role") != required_role:
                return jsonify({"error": "Forbidden"}), 403

            # attach user info
            g.user = decoded
            return f(*args, **kwargs)
        return wrapper
    return decorator
