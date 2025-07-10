from flask import Flask
from routes.auth import auth_bp
from routes.tasks import tasks_bp

app = Flask(__name__)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(tasks_bp, url_prefix='/tasks')


if __name__ == '__main__':
    app.run(debug=True)
