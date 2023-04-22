FROM python:3.7.5

# ARG app_dir=/app/

# ADD requirements.txt $app_dir

# ADD app.py $app_dir

# WORKDIR $app_dir
WORKDIR /usr/src/app
COPY /requirements.txt ./

RUN pip install --upgrade pip

# 利用するパッケージがかたまるまでコメントアウトしてても良さそう
RUN pip install -r requirements.txt
