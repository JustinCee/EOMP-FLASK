from flask import Flask, request
import hmac
import sqlite3

from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS

app = Flask(__name__)


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def fetch_users():
    with sqlite3.connect('sales.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4]))
    return new_data


def init_user_table():
    conn = sqlite3.connect('sales.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "cell_number TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


def init_item_table():
    with sqlite3.connect('sales.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "title TEXT NOT NULL,"
                     "category TEXT NOT NULL,"
                     "quantity TEXT NOT NULL,"
                     "total TEXT NOT NULL,"
                     "cost TEXT NOT NULL)")
    print("item table created successfully.")


init_user_table()
init_item_table()
users = fetch_users()

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'this-should-be-a-secret'
CORS(app)

jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


@app.route('/register/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        cell = request.form['cell_number']
        password = request.form['password']

        with sqlite3.connect("sales.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users("
                           "first_name,"
                           "last_name,"
                           "username,"
                           "cell_number,"
                           "password) VALUES(?, ?, ?, ?, ?)", (first_name, last_name, username, cell, password))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 200
        return response


@app.route('/product-create/', methods=['POST'])
@jwt_required()
def products_create():
    response = {}

    if request.method == "POST":

        title = request.form['title']
        category = request.form['category']
        quantity = request.form['quantity']
        cost = request.form['cost']
        total = int(cost) * int(quantity)

        with sqlite3.connect('sales.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO items (title, category, quantity,"
                           "cost, total) VALUES(?, ?, ?, ?, ?)", (title, category, quantity, cost, total))
            conn.commit()
            response['message'] = "item added successfully"
            response['status_code'] = 201
        return response


@app.route('/get-products/', methods=['GET'])
def get_products():
    response = {}
    with sqlite3.connect('sales.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items")
        carts = cursor.fetchall()

    response['status_code'] = 201
    response['data'] = carts
    return response


if __name__ == "__main__":
    app.debug = True
    app.run()
