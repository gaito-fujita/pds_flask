import os
from flask import Flask
from .routes import bp
from .models import db
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import PyMongo
from .mongo import mongo


def create_app(config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://{user}:{password}@{host}/{db_name}?charset=utf8'.format(**{
        'user': "root",
        'password': "root",
        'host': "mysql:3306",
        'db_name': "mydatabase"
    })
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'secret'
    app.config['MONGO_URI'] = 'mongodb://root:password@mongo:27017/my_database?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false'
    # load environment configuration
    if 'WEBSITE_CONF' in os.environ:
        app.config.from_envvar('WEBSITE_CONF')

    # load app specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)

    @app.before_first_request
    def create_tables():
        db.create_all()
    db.init_app(app)
    mongo.init_app(app)

    app.register_blueprint(bp, url_prefix='')
    return app

app=create_app()

