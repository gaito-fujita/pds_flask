docker-compose build
docker-compose up -d
docker exec -it admin_server bash
flask run --host=0.0.0.0

mysql -u root -p -h 127.0.0.1
->password : root
show databases;
もしmydatabaseがなければ->create database mydatabase;を実行

flaskからmysqlに接続したい場合は、異なるコンテナ間で通信を行うことになるので、dockerネットワークを作っておく必要がある。詳細はadmin_serverのapp.pyにおけるmysqlへの接続の所とymlを見る。
またなぜか最初からmydatabaseは作成されない。

sqliteではテーブルを作成する前に外部キー制約を定義することができるが、MySQLではできない。
->先にテーブルを作成する必要がある。

mongoも自分でデータベース、コレクションの作成が必要
mongodb://root:*****@localhost:27016/mydatabase?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false