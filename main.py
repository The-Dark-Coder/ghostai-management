from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'your_secret_key'
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Set the login view to redirect unauthorized users to the login page

# UserLoader class to handle user login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# User loader function to load user by ID
@login_manager.user_loader
def load_user(user_id):
    if user_id == 'admin':
        return User(user_id)
    return None

# MongoDB connection
mongo_url = 'mongodb+srv://ghostai:ghostai@ghostai.4bni5mt.mongodb.net/your_database_name?retryWrites=true&w=majority'
client = MongoClient(mongo_url)
db = client.get_database('your_database_name')  # Specify your database name
users_collection = db.users  # Specify your collection name



def get_database_metrics():
    # Fetch the database statistics
    db_stats = db.command("dbstats")
    
    # Calculate the percentage of the database full based on storageSize and dataSize
    storage_size = db_stats.get('storageSize', 0)
    data_size = db_stats.get('dataSize', 0)
    
    if storage_size > 0:
        database_percentage = (data_size / storage_size) * 100
    else:
        database_percentage = 0
    
    return round(database_percentage, 2)


def get_user_metrics():
    # Count the total number of users in the collection
    total_users = users_collection.count_documents({})
    return total_users

# Routes
@app.route('/')
@login_required
def index():
    # Fetch database and user metrics
    database_percentage = get_database_metrics()
    total_users = get_user_metrics()
    
    # Pass metrics to the template
    return render_template('index.html', database_percentage=database_percentage, total_users=total_users)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if username and password are correct
        if username == 'admin' and password == 'admin':
            # Log in the user
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        else:
            return 'Invalid username or password'

    return render_template('login.html')


@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    username = data['username']
    password = data['password']
    pro = data['pro'] if 'pro' in data else False
    
    if users_collection.find_one({'username': username}):
        return jsonify({"message": "User already exists"})
    
    users_collection.insert_one({'username': username, 'password': password, 'pro': pro})
    return jsonify({"message": "User added successfully"})


@app.route('/metrics',methods=['GET'])
def metrics():
    return jsonify({"database_percentage": get_database_metrics(), "total_users": get_user_metrics()})

@app.route('/delete_user', methods=['POST'])
def delete_user():
    data = request.json
    username = data['username']
    
    result = users_collection.delete_one({'username': username})
    
    if result.deleted_count == 1:
        return jsonify({"message": "User deleted successfully"})
    else:
        return jsonify({"message": "User not found"})

@app.route('/edit_user', methods=['POST'])
def edit_user():
    data = request.json
    username = data['username']
    pro = data['pro']
    
    result = users_collection.update_one({'username': username}, {'$set': {'pro': pro}})
    
    if result.modified_count == 1:
        return jsonify({"message": "User updated successfully"})
    else:
        return jsonify({"message": "User not found"})

@app.route('/search_user', methods=['POST'])
def search_user():
    data = request.json
    username = data['username']
    
    user = users_collection.find_one({'username': username}, {'_id': 0})
    
    if user:
        return jsonify(user)
    else:
        return jsonify({"message": "User not found"})

@app.route('/user_list')
def user_list():
    users = list(users_collection.find({}, {'_id': 0}))
    return jsonify(users)

if __name__ == '__main__':
    app.run(debug=True)