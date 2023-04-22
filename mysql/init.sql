-- 先にテーブルを作成しておくためのSQL文を書いておく

CREATE TABLE data_category (
        id INTEGER(11) NOT NULL AUTO_INCREMENT,
        category VARCHAR(255),
        PRIMARY KEY (id),
        UNIQUE (category)
);

CREATE TABLE user (
    id INT(11) NOT NULL AUTO_INCREMENT,
    username VARCHAR(255) UNIQUE,
    PRIMARY KEY (id)
);

CREATE TABLE client (
    id INT(11) NOT NULL AUTO_INCREMENT,
    user_id INT(11),
    client_id VARCHAR(255),
    client_secret VARCHAR(255),
    PRIMARY KEY (id),
    UNIQUE KEY client_id (client_id),
    UNIQUE KEY client_secret (client_secret),
    CONSTRAINT client_user_id_fk
        FOREIGN KEY (user_id)
        REFERENCES user (id)
        ON DELETE CASCADE
);

CREATE TABLE data_group (
    id INT NOT NULL AUTO_INCREMENT,
    sql VARCHAR(255),
    search_user_id INTEGER,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(search_user_id) REFERENCES user (id) ON DELETE CASCADE
);

CREATE TABLE consent_list (
    id INT(11) NOT NULL AUTO_INCREMENT,
    user_id INTEGER,
    data_group_id INTEGER,
    consent BOOLEAN DEFAULT false,
    client_id VARCHAR(255),
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES user (id) ON DELETE CASCADE,
    FOREIGN KEY(data_group_id) REFERENCES data_group (id) ON DELETE CASCADE,
    FOREIGN KEY(client_id) REFERENCES client (client_id) ON DELETE CASCADE
);

CREATE TABLE data_info (
    id INT(11) NOT NULL AUTO_INCREMENT,
    category_id INT(11),
    data_id VARCHAR(255),
    user_id INT(11),
    timestamp_ DATETIME,
    insert_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (data_id),
    FOREIGN KEY (category_id) REFERENCES data_category(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);
