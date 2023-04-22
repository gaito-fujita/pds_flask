from flask import Blueprint,render_template,request,session,redirect
from .models import db,Memo,Category,Info,User,Client,Group,Consent
from datetime import datetime
import pytz
from .mongo import mongo
import requests
from requests.auth import HTTPBasicAuth
import base64
import json
from flask_pymongo import ObjectId

bp = Blueprint('home', __name__)

jst = pytz.timezone('Asia/Tokyo')

def current_user():
    if 'id' in session:
        uid = session['id']
        return User.query.get(uid)
    return None

# #curl -d "memo=test_memo" -X POST http://localhost:5001/insert
# @bp.route("/insert", methods=["POST"])
# def insert():
#     # postの受け取り
#     memo_txt = request.form["memo"]
#     # Memoの生成
#     memo = Memo(memo=memo_txt)
#     # MemoをDBに反映
#     db.session.add(memo)
#     db.session.commit()

#     return "insert ok"

# #curl localhost:5001/select
# @bp.route("/select", methods=["GET"])
# def select():
#     memos = Memo.query.all()
#     return memos.memo

# @bp.route("/test",methods=["GET"])
# def test():
#     category = Category(category="A")
#     db.session.add(category)
#     db.session.commit()
#     info = Info(category_id=1)
#     db.session.add(info)
#     db.session.commit()
#     return "test_ok"

#ログインページ
@bp.route("/login",methods=('GET', 'POST'))
def login():
    if request.method=="GET":
        user = current_user()
        if user:
            return redirect('/home')
        return render_template('login.html')
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
            user_register(username)
        session['id'] = user.id
        return redirect('/home')

@bp.route('/logout')
def logout():
    del session['id']
    return redirect('/login')

#ホーム
@bp.route("/home",methods=['GET'])
def home():
    user = current_user()
    if not user:
        return redirect("/login")
    return render_template('home.html',user=user)

#データの保管 {"name": "John"}
@bp.route("/store",methods=('GET', 'POST'))
def store():
    user = current_user()
    if not user:
        return redirect("/login")
    if request.method == 'GET':
        return render_template('store.html',user = user)
    if request.method == 'POST':
        data = request.form.get('data')
        data = json.loads(data)
        data_id = mongo_insert(data)
        data_id = str(data_id)
        category = request.form.get('category')
        timestamp_ = request.form.get('timestamp_')
        if not timestamp_:
            timestamp_ = datetime.now(jst)
        if Info.query.filter_by(data_id=data_id).first():
            print("すでにデータあり")
            return redirect("/home")
        if not Category.query.filter_by(category=category).first():
            data_category = Category(category=category)
            db.session.add(data_category)
            db.session.commit()
        data_category = Category.query.filter_by(category=category).first()
        data_info = Info(
            category_id = data_category.id,
            data_id = data_id,
            user_id = user.id,
            timestamp_= timestamp_,
            insert_at = datetime.now(jst)
            )
        db.session.add(data_info)
        db.session.commit()
        print("保存完了")
        return redirect("/home")

#データの検索
@bp.route("/search",methods=('GET','POST'))
def search():
    user = current_user()
    if not user:
        return redirect("/login")
    data_categorys = Category.query.all()
    if request.method == 'GET':
        return render_template('search.html',user = user,data_categorys = data_categorys)
    if request.method == 'POST':
        #リクエストの作成
        if request.form.get('make_request'):
            timestamp_1 = request.form.get('timestamp_1')
            timestamp_2 = request.form.get('timestamp_2')
            search_category = request.form.get('search_category')
            if timestamp_1:
                sql = {
                    "search_category": search_category,
                    "timestamp_1": timestamp_1,
                    "timestamp_2": timestamp_2
                }
                data_category= Category.query.filter_by(category=search_category).first()
                count_users = Info.query.filter_by(
                    category_id = data_category.id
                ).filter(
                    Info.timestamp_ >= timestamp_1,
                    Info.timestamp_ <= timestamp_2
                    ).all()
            else:
                sql = {
                    "search_category": search_category
                }
                data_category= Category.query.filter_by(category=search_category).first()
                count_users = Info.query.filter_by(category_id = data_category.id).all()
            now = datetime.now(jst)
            data_group = Group(sql=str(sql),search_user_id=user.id,created_at=now)
            db.session.add(data_group)
            db.session.flush()
            db.session.commit()
            count=0
            for count_user in count_users:
                count+=1
                count_username = User.query.filter_by(id=count_user.user_id).first().username
                client_str = create_client(count_username,user.username)
                client_split_str = client_str.split(",")
                client_data = Client(user_id=user.id,client_id=client_split_str[0],client_secret=client_split_str[1])
                db.session.add(client_data)
                db.session.flush()
                db.session.commit()
                consent_list = Consent(user_id=count_user.user_id,data_group_id=data_group.id,consent=False,client_id=client_split_str[0])
                db.session.add(consent_list)
                db.session.commit()
            return render_template('create_client.html',user=user,sql=str(sql),count=count)
        else:
            #該当者の提示
            search_category = request.form.get('category')
            timestamp_1 = request.form.get('timestamp_1')
            timestamp_2 = request.form.get('timestamp_2')
            data_category= Category.query.filter_by(category=search_category).first()
            if timestamp_1:
                count_user = Info.query.filter_by(
                    category_id = data_category.id
                ).filter(
                    Info.timestamp_ >= timestamp_1,
                    Info.timestamp_ <= timestamp_2
                    ).count()
            else:
                count_user = Info.query.filter_by(category_id = data_category.id).count()
            return render_template('search.html',
                user = user,
                data_categorys = data_categorys,
                count_user = count_user,
                search_category = search_category,
                timestamp_1 = timestamp_1,
                timestamp_2 = timestamp_2
                )
            

#リクエストリストの閲覧
@bp.route("/req_list",methods=('GET','POST'))
def req_list():
    user = current_user()
    if not user:
        return redirect("/login")
    if request.method=='POST':
        consent_list_id = request.form.get("consent_list_id")
        consent = request.form.get("consent")
        if consent == "1":
            # consent_list更新,authorize,token
            consent_list = Consent.query.filter_by(id=consent_list_id).first()
            consent_list.consent = True
            client = Client.query.filter_by(client_id=consent_list.client_id).first()
            client_id = client.client_id
            client_secret = client.client_secret
            sql = Group.query.filter_by(id=consent_list.data_group_id).first().sql
            db.session.commit()
            code = authorize(user.username,client_id)
            issue_token(client_id,client_secret,code)
        else:
            # consent_list更新,revoke
            consent_list = Consent.query.filter_by(id=consent_list_id).first()
            consent_list.consent = False
            db.session.commit()
            tokens = get_tokens(consent_list.client_id)
            tokens = tokens[1:]
            tokens = tokens.split("?")
            client = Client.query.filter_by(client_id=consent_list.client_id).first()
            for token in tokens:
                revoke(token,client.client_id,client.client_secret)

    #consent_listの表示
    consent_lists = Consent.query.filter_by(user_id=user.id).all()
    data_groups = []
    search_users = []
    num = 0
    for consent_list in consent_lists:
        num+=1
        data_group = Group.query.filter_by(id=consent_list.data_group.id).first()
        data_groups.append(data_group)
        search_user = User.query.filter_by(id=data_group.search_user_id).first()
        search_users.append(search_user)
    return render_template(
        'req_list.html',
        user=user,
        data_groups=data_groups,
        consent_lists=consent_lists,
        search_users=search_users,
        num=num
        )

#所持トークンの閲覧
@bp.route("/tokens",methods=('GET','POST'))
def tokens():
    user = current_user()
    if not user:
        return redirect("/login")
    clients = Client.query.filter_by(user_id=user.id).all()
    client_ids = []
    sqls = []
    for client in clients:
        client_ids.append(client.client_id)
    client_ids_str = ""
    for client_id in client_ids:
        consent_list = Consent.query.filter_by(client_id=client_id).first()
        if consent_list.consent == True:
            client_ids_str+=","+client_id
            data_group = Group.query.filter_by(id=consent_list.data_group_id).first()
            sqls.append(data_group.sql)
    client_ids_str = client_ids_str[1:]
    tokens = get_tokens(client_ids_str)
    tokens = tokens[1:]
    tokens = tokens.split("?")
    num=len(tokens)
    if request.method == 'POST':
        i = request.form.get('num')
        access_token = request.form.get('access_token')
        consent_list = Consent.query.filter_by(client_id=client_ids[int(i)]).first()
        data_group = Group.query.filter_by(id=consent_list.data_group_id).first()
        sql = data_group.sql
        if use_access_token(access_token)=="ok":
            sql = json.loads(sql.replace("'", "\""))
            search_category = sql["search_category"]
            data_category= Category.query.filter_by(category=search_category).first()
            if "timestamp_1" in sql:
                data_infos = Info.query.filter_by(
                    category_id = data_category.id,
                    user_id = consent_list.user_id
                ).filter(
                    Info.timestamp_ >= sql["timestamp_1"],
                    Info.timestamp_ <= sql["timestamp_2"]
                    ).count()
            else:
                data_infos = Info.query.filter_by(user_id = consent_list.user_id,category_id = data_category.id).all()
            datas = []
            for data_info in data_infos:
                data = mongo_find(data_info.data_id)
                datas.append(data)
            return render_template('tokens.html',user=user,tokens=tokens,scopes=sqls,num=num,client_ids=client_ids,datas=datas)
    return render_template('tokens.html',user=user,tokens=tokens,scopes=sqls,num=num,client_ids=client_ids)

@bp.route("/test",methods=['GET'])
def test():
    return use_access_token("ax1QslFJhJyBL43Hu2g1hkKpGVovK72WeirzdQY1M1")

def mongo_insert(data):
    result = mongo.db.my_collection.insert_one(data)
    return result.inserted_id

def mongo_find(id):
    return mongo.db.my_collection.find_one({'_id': ObjectId(id)})

def user_register(username):
    data = {
        'username': username
    }
    response=requests.post('http://authorization_server:5000/user_register',data=data)
    return response.text

def to_bytes(x, charset='utf-8', errors='strict'):
    if x is None:
        return None
    if isinstance(x, bytes):
        return x
    if isinstance(x, str):
        return x.encode(charset, errors)
    if isinstance(x, (int, float)):
        return str(x).encode(charset, errors)
    return bytes(x)

def to_unicode(x, charset='utf-8', errors='strict'):
    if x is None or isinstance(x, str):
        return x
    if isinstance(x, bytes):
        return x.decode(charset, errors)
    return str(x)

def create_basic_header(username, password):
        text = '{}:{}'.format(username, password)
        auth = to_unicode(base64.b64encode(to_bytes(text)))
        return {'Authorization': 'Basic ' + auth}

def create_client(username,client_name):
    data = {
        'username': username,
        'client_name': client_name,
        'client_uri': "http://localhost",
        'grant_types': "authorization_code\nrefresh_token",
        'redirect_uris': "http://localhost",
        'response_types': "code",
        'scope': "profile",
        'token_endpoint_auth_method': "client_secret_basic"
    }
    response=requests.post('http://authorization_server:5000/create_client',data=data)
    return response.text

def authorize(username,client_id):#client_idは文字列
    username = username
    client_id = client_id
    response_type = "code"
    scope = "profile"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    params = {
        'username': username,
        'client_id': client_id,
        'response_type': response_type,
        'scope': scope
    }
    response=requests.post('http://authorization_server:5000/oauth/authorize',params=params)
    return response.text

def issue_token(client_id,client_secret,code):
    grant_type = "authorization_code"
    scope = "profile"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        "code": code,
        "grant_type": grant_type,
        "scope": scope
    }
    response = requests.post(
        'http://authorization_server:5000/oauth/token',
        headers=headers,
        data=data,
        auth=HTTPBasicAuth(client_id,client_secret)
        )
    return response.text

#client_idsは,区切りの文字列
#返り値は、?token?token@?scope?scope
def get_tokens(client_ids):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        "client_ids": client_ids
    }
    response = requests.post(
        'http://authorization_server:5000/get_tokens',
        headers=headers,
        data=data
        )
    return response.text

#アクセストークンの失効
def revoke(access_token,client_id,client_secret):
    headers=create_basic_header(client_id,client_secret)
    data={
        "token":access_token
        }
    response=requests.post(
        'http://authorization_server:5000/oauth/revoke',
        headers=headers,
        data=data,
        auth=HTTPBasicAuth(client_id, client_secret)
        )
    return response.text

#アクセストークンの使用
def use_access_token(access_token):
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    response=requests.get('http://authorization_server:5000/use_token',headers=headers)
    return response.text

# @bp.route("/create_client_test",methods=['GET'])
# def create_client_test():
#     username = "gaito"
#     client_name = "He"
#     client_uri = "http://localhost"
#     grant_types = "authorization_code\nrefresh_token"
#     redirect_uris = "http://localhost"
#     response_types = "code"
#     scope = "profile"
#     token_endpoint_auth_method = "client_secret_basic"
#     data = {
#         'username': username,
#         'client_name': client_name,
#         'client_uri': client_uri,
#         'grant_types': grant_types,
#         'redirect_uris': redirect_uris,
#         'response_types': response_types,
#         'scope': scope,
#         'token_endpoint_auth_method': token_endpoint_auth_method
#     }
#     response=requests.post('http://authorization_server:5000/create_client',data=data)
#     return "create_client_test"

# @bp.route("/authorize_test",methods=['GET'])
# def authorize_test():
#     username = "gaito"
#     client_id = "g4sUjR3dUCLH1fY0mdwOTrlx"
#     response_type = "code"
#     scope = "profile"
#     headers = {
#         'Accept': 'application/json',
#         'Content-Type': 'application/x-www-form-urlencoded'
#     }
#     params = {
#         'username': username,
#         'client_id': client_id,
#         'response_type': response_type,
#         'scope': scope
#     }
#     response=requests.post('http://authorization_server:5000/oauth/authorize',params=params)
#     return "authorize_test"

# @bp.route("/issue_token",methods=['GET'])
# def issue_token():
#     client_id = "g4sUjR3dUCLH1fY0mdwOTrlx"
#     client_secret = "VWk423zFJAeFCrmghbT4ViUF6OKolCNFrMkwGIeFXCZXBw9M"
#     grant_type = "authorization_code"
#     code = "kv4v94OwwKACujtRzidAFRd1fMFvuoefe4XMoagdvhXBjKev"
#     scope = "profile"
#     headers = {
#         'Accept': 'application/json',
#         'Content-Type': 'application/x-www-form-urlencoded'
#     }
#     data = {
#         "code": code,
#         "grant_type": grant_type,
#         "scope": scope
#     }
#     response = requests.post(
#         'http://authorization_server:5000/oauth/token',
#         headers=headers,
#         data=data,
#         auth=HTTPBasicAuth(client_id,client_secret)
#         )
#     return response.text

# @bp.route("/get_tokens",methods=['GET'])
# def get_tokens():
#     client_ids = "g4sUjR3dUCLH1fY0mdwOTrlx,ZGozSicKbe71W3tXedlygNkF"
#     headers = {
#         'Accept': 'application/json',
#         'Content-Type': 'application/x-www-form-urlencoded'
#     }
#     data = {
#         "client_ids": client_ids
#     }
#     response = requests.post(
#         'http://authorization_server:5000/get_tokens',
#         headers=headers,
#         data=data
#         )
#     return response.text


