import time
from flask import Blueprint, request, session, url_for
from flask import render_template, redirect, jsonify,url_for
from werkzeug.security import gen_salt
from authlib.integrations.flask_oauth2 import current_token
from authlib.oauth2 import OAuth2Error
from .models import db, User, OAuth2Client,OAuth2Token,OAuth2AuthorizationCode
from .oauth2 import authorization, require_oauth
import json
import datetime,time
import requests
from requests.auth import HTTPBasicAuth


bp = Blueprint('home', __name__)


def current_user():
    if 'id' in session:
        uid = session['id']
        return User.query.get(uid)
    return None


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]

##アクセストークンが現在有効であるか否か
def check_token_valid(token):
    return token.access_token_revoked_at==0 and (not token.is_expired())


#ユーザ登録
#username
#curl -X POST -F 'username=gaito' localhost:5002/user_register
@bp.route('/user_register',methods=['POST'])
def user_register():
    username = request.form.get('username')
    user = User(username=username)
    db.session.add(user)
    db.session.commit()
    return "user_register"


#client作成
#username,client_name,client_uri,grant_types,redirect_uris
#response_types,scope,token_endpoint_auth_method
@bp.route('/create_client',methods=['POST'])
def create_client():
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    client_id = gen_salt(24)
    client_id_issued_at = int(time.time())
    client = OAuth2Client(
        client_id=client_id,
        client_id_issued_at=client_id_issued_at,
        user_id=user.id,
    )
    form = request.form
    client_metadata = {
        "client_name": form["client_name"],
        "client_uri": form["client_uri"],
        "grant_types": split_by_crlf(form["grant_types"]),
        "redirect_uris": split_by_crlf(form["redirect_uris"]),
        "response_types": split_by_crlf(form["response_types"]),
        "scope": form["scope"],
        "token_endpoint_auth_method": form["token_endpoint_auth_method"]
    }
    
    client.set_client_metadata(client_metadata)
    if form['token_endpoint_auth_method'] == 'none':
        client.client_secret = ''
    else:
        client.client_secret = gen_salt(48)

    db.session.add(client)
    db.session.flush()
    db.session.commit()
    
    return client.client_id+","+client.client_secret


#認可コード発行
#username,client_id,response_type,scope
@bp.route('/oauth/authorize', methods=['GET','POST'])
def authorize():
    username = request.args.get('username')
    client_id = request.args.get('client_id')
    scope = request.args.get('scope')
    grant_user = User.query.filter_by(username=username).first()
    authorization.create_authorization_response(grant_user=grant_user)
    code = OAuth2AuthorizationCode.query.filter_by(
        user_id=grant_user.id,
        client_id=client_id,
        scope=scope
        ).order_by(OAuth2AuthorizationCode.id.desc()).first()
    return code.code
    

#アクセストークン発行
#client_id,client_secret,grant_type,code,scope
@bp.route('/oauth/token',methods=['POST'])
def issue_token():
    return authorization.create_token_response()


#所持しているアクセストークン
@bp.route('/get_tokens',methods=['POST'])
def get_tokens():
    client_ids_str = request.form.get('client_ids')
    client_ids = client_ids_str.split(",")
    access_tokens = ""
    for client_id in client_ids:
        tokens = OAuth2Token.query.filter_by(client_id=client_id).all()
        for token in tokens:
            if token.access_token_revoked_at==0:
                access_tokens+="?"+str(token.access_token)
    return str(access_tokens)

#アクセストークン失効
@bp.route('/oauth/revoke', methods=['POST'])
def revoke_token():
    return authorization.create_endpoint_response('revocation')

#アクセストークンの使用
@bp.route('/use_token')
@require_oauth('profile')
def api_me():
    return "ok"
    

