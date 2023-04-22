from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR,BOOLEAN,DATETIME

# dbの初期化
db = SQLAlchemy()

class Memo(db.Model):
    """
        Memoモデルの定義
    """
    __tablename__ = "memos"

    id = db.Column("id", INTEGER(11), primary_key=True,autoincrement=True)
    memo = db.Column("memo", VARCHAR(255), nullable=True)

class Category(db.Model):
    __tablename__="data_category"

    id = db.Column("id",INTEGER(11),primary_key=True,autoincrement=True)
    category = db.Column("category", VARCHAR(255), nullable=True,unique=True)

class User(db.Model):
    __tablename__="user"

    id = db.Column("id",INTEGER(11),primary_key=True,autoincrement=True)
    username = db.Column("username", VARCHAR(255), nullable=True,unique=True)

class Client(db.Model):
    __tablename__="client"

    id = db.Column("id",INTEGER(11),primary_key=True,autoincrement=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')
    client_id = db.Column("client_id", VARCHAR(255), nullable=True,unique=True)
    client_secret = db.Column("client_secret", VARCHAR(255), nullable=True,unique=True)

class Group(db.Model):
    __tablename__="data_group"

    id = db.Column("id",INTEGER(11),primary_key=True,autoincrement=True)
    sql = db.Column("sql", VARCHAR(255), nullable=True)
    search_user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')
    created_at = db.Column("created_at",DATETIME, nullable=False)

class Consent(db.Model):
    __tablename__="consent_list"

    id = db.Column("id",INTEGER(11),primary_key=True,autoincrement=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')
    data_group_id = db.Column(
        db.Integer, db.ForeignKey('data_group.id', ondelete='CASCADE'))
    data_group = db.relationship('Group')
    consent = db.Column("consent",BOOLEAN,default=False)
    client_id = db.Column(
        db.String(255), db.ForeignKey('client.client_id', ondelete='CASCADE'))
    client = db.relationship('Client')

class Info(db.Model):
    __tablename__="data_info"

    id = db.Column("id",INTEGER(11),primary_key=True,autoincrement=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey('data_category.id', ondelete='CASCADE'))
    data_category = db.relationship('Category')
    data_id = db.Column("data_id", VARCHAR(255), nullable=False,unique=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')
    timestamp_ = db.Column("timestamp_",DATETIME,nullable=True)
    insert_at = db.Column("insert_at",DATETIME, nullable=False)

