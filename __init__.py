#! Python 3.6


#  Flask modules from flask library
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response
from flask import session as login_session

# SQL Alchemy modules
from sqlalchemy import create_engine, asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
# from databasesetup import Category, Item, User
from databasesetup_pg import Users, Category, Items

# Authentication modules for google OAuth
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

import random
import string
import json
import requests

# Postgres DB Access
from sqlalchemy.dialects import postgresql
import psycopg2

# ''' 
# Enable Foreign Key Support Using Passive Deletes
# https://docs.sqlalchemy.org/en/latest/orm/collections.html#using-passive-deletes
# Implementing ON DELETE CASCADE
# https://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#sqlite-foreign-keys
# '''
# from sqlite3 import Connection as SQLite3Connection
# from sqlalchemy import event
# from sqlalchemy.engine import Engine


# @event.listens_for(Engine, "connect")
# def _set_sqlite_pragma(dbapi_connection, connection_record):
#     if isinstance(dbapi_connection, SQLite3Connection):
#         cursor = dbapi_connection.cursor()
#         cursor.execute("PRAGMA foreign_keys=ON;")
#         cursor.close()

from sqlalchemy.ext.declarative import declarative_base  
# from sqlalchemy.dialects.postgresql import 

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Sporting Goods Catalog App"


# engine = create_engine('sqlite:///sportscatalogitems.db', connect_args={'check_same_thread': False})
# Create engine for Postgres
DBNAME = "sportscatalogitems"
USER="sportscatalogitems"
PASSWORD="1234"
HOST="localhost"
PORT="5432"

# engine = create_engine('postgresql+psycopg2://USER:PASSWORD@HOST/DBNAME')
engine = create_engine("postgresql://sportscatalogitems:1234@localhost:5432/sportscatalogitems")
base = declarative_base()

DBSession = sessionmaker(bind=engine)
session = DBSession()

base.metadata.create_all(engine)

# # **************************************
# def users():
#     print("Inside Users ... OK")
#     users_count = session.query(Users).count()
#     print(users_count)
#     users_direct_sql = session.query("Select * from Users Order By Users.user_id").all
#     print(users_direct_sql)
#     # for row in users_direct_sql:
#     #     print(users_direct_sql.user_id)

#     users = session.query(Users).order_by(Users.user_id).all()
#     print(users)
#     for user in users:
#         print("Users Are :", {user.user_id}, {user.user_name})

# def show_categories():
#     recentitems_count = (session.query(Items).order_by(Items.item_id.desc()).count())
#     print("Count of items is --- : ",recentitems_count)

#     categories = (session.query(Category).order_by(Category.category_name).all())
#     for category in categories:
#         print({category.category_id},  {category.category_name})
    
#     recentitems = (session.query(Items).order_by(Items.item_id.desc()).limit(10))

# users()
# show_categories()

# # **************************************

# **** OAuth **** Create anti-forgery state token
@app.route('/login')
def showlogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for _ in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)
    # return "The current session state is %s" % login_session['state']


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid. Converted to python 3 using requests instead of httplib2
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}'.format(access_token))
    token_url = requests.get(url=url)
    result = json.loads(token_url.text)
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    g_id = credentials.id_token['sub']
    if result['user_id'] != g_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
        json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_g_id = login_session.get('g_id')
    if stored_access_token is not None and g_id == stored_g_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['g_id'] = g_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Check for existing/new user
    user_id = get_user_id(login_session['email'])
    if not user_id:
       new_user_id = create_user(login_session)
       login_session['user_id'] = new_user_id
    else:
        login_session['user_id'] = user_id

    output = b''
    output += b'<h1>Welcome, '
    output += bytes(login_session['username'], encoding="utf-8")
    output += b'!</h1>'
    output += b'<img src="'
    output += bytes(login_session['picture'], encoding="utf-8")
    output += b' " style = "width: 300px; height: 300px;border-radius: 150px;' \
              b'-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output

# END gconnect() 


# User details
def create_user(login_session):
    newuser = Users(user_name=login_session['username'], user_email=login_session['email'],
                   user_picture=login_session['picture'])
    session.add(newuser)
    try:
        session.commit()

        user = session.query(Users).filter_by(user_email=login_session['email']).one()
        return user.user_id
    except SQLAlchemyError as _:
        session.rollback()
        return "Database Commit Exception: Create User - Unable to commit changes"
    finally:
        session.close()



def get_user_info(user_id):
    try:
        user = session.query(Users).filter_by(user_id=user_id).one()
        return user
    except SQLAlchemyError as _:
        return "Database Select Exception: getUserInfo"


def get_user_id(email):
    try:
        user = session.query(Users).filter_by(user_email=email).one()
        return user.user_id
    except SQLAlchemyError as _:
        return "Database Select Exception: getUserID"
# User Details END


# START gdisconnect() - DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    try:
        access_token = login_session.get('access_token')
    except KeyError:
        flash('Failed to get access token')
        return redirect(url_for('show_categories'))
    if access_token is None:

        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # Check that the access token is valid. Converted to python 3 using requests instead of httplib2
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}'.format(access_token))
    token_url = requests.get(url=url)
    result = json.loads(token_url.text)
   
    if result is None:
        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        del login_session['access_token']
        del login_session['g_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'

        flash('Google Sign Out - Successfull!!')
 
        return response

    
# END OAuth **** gdisconnect()


# Check login status
def loginstatus():
    if 'access_token' in login_session:
        login_status = True
    else:
        login_status = False
    return login_status


# Home Page without Login - Show all Categories and Recent 10 Items Added
@app.route('/')
@app.route('/home/', methods=['GET', 'POST'])
def home():
    recentitems_count = (session.query(Items).order_by(Items.item_id.desc()).count())
    print("Count of items is --- : ",recentitems_count)

    categories = (session.query(Category).order_by(Category.category_name).all())
    for category in categories:
        print({category.category_id},  {category.category_name})
    
    recentitems = (session.query(Items).order_by(Items.item_id.desc()).limit(10))
    
    for items in recentitems:
        print("Recent Ites Added is : ",{items.item_id}, {items.item_name})
    
    login_status = loginstatus()
    if login_status is True:
        return render_template('categories.html', categories=categories, recentItemsAdded=recentitems)
    else:
        return render_template('home.html', categories=categories, recentItemsAdded=recentitems)
    

# **** START CATEGORY ****


# Show all categories
@app.route('/category/')
def show_categories():
    login_status = loginstatus()
    if login_status is True:
        categories = (session.query(Category).order_by(Category.category_name).all())
        print(categories)
        recentitems = (session.query(Items).order_by(Items.item_id.desc()).limit(10))
        print(recentitems)
        return render_template('categories_only.html', categories=categories, recentItemsAdded=recentitems)
        
    else:
        flash('LOGIN!!: Feature requires login. Please log in. You are redirected to the home page...')
        return redirect(url_for('home'))


# Check if the category alredy exists
def check_category_name(category_name_exists):
    try:
        categoryquery = (session.query(Category).filter_by(category_name=category_name_exists).one())
        if categoryquery.category_name == category_name_exists:
            name_exists = True
        else:
            name_exists = False
    except SQLAlchemyError as _:
        return "Database Select Exception: checkCategoryNameExists"
    return name_exists
            

# Create a new category
@app.route('/category/new/', methods=['GET', 'POST'])
def new_category():
    login_status = loginstatus()
    if login_status is True:
        if request.method == 'POST':
            addcategory = Category(category_name=request.form['name'], user_id=login_session['user_id'])
            if check_category_name(addcategory.category_name) is True:
                flash('DUPPLICATE CATEGORY!!: " %s " ...category name already exists' % addcategory.category_name)
                return redirect(url_for('show_categories'))
            else:

                session.add(addcategory)
                try:
                    session.commit()
                    flash('CREATE SUCCESS!!: " %s " ...new category added' % addcategory.category_name)
                    return redirect(url_for('show_categories'))
                except SQLAlchemyError as _:
                    return "Database Commit Exception: newCategory"

                finally:
                    session.close()
        else:
            return render_template('newCategory.html')
    else:
        flash('LOGIN!!: Feature requires login. Please log in. You are redirected to the home page...')
        return redirect(url_for('home'))


# Edit a category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def edit_category(category_id):
    login_status = loginstatus()
    if login_status is True:
        edit_query = session.query(Category).filter_by(category_id=category_id).one()
        if edit_query.user_id != login_session['user_id']:
            flash('EDIT NOT ALLOWED!!: " %s " ...creator alone has permission to edit' % edit_query.category_name)
            return redirect(url_for('show_categories'))

        if request.method == 'POST':
            
            if request.form['name']:
                edit_query.category_name = request.form['name']
                session.add(edit_query)
                try:
                    session.commit()
                    flash('EDIT SUCCESS!!: " %s " ...category modified' % edit_query.category_name)
                    return redirect(url_for('show_categories'))
                except SQLAlchemyError as _:
                    flash('EDIT EXCEPTION OCCURRED!! Unable to edit. Something went wrong when saving the changes...')
                    return redirect(url_for('show_categories'))
                finally:
                    session.close() 
        else:
            return render_template('editcategory.html', category=edit_query)
    else:
        flash('LOGIN!!: Feature requires login. Please log in. You are redirected to the home page...')
        return redirect(url_for('home'))
    

# Delete a category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def delete_category(category_id):
    login_status = loginstatus()
    if login_status is True:
        delete_query = session.query(Category).filter_by(category_id=category_id).one()
        items = session.query(Items).filter_by(category_id=category_id).all()
        if delete_query.user_id != login_session['user_id']:
                flash('DELETE NOT ALLOWED!!: " %s " ...creator alone has permission to delete'
                      % delete_query.category_name)
                return redirect(url_for('show_categories'))

        if request.method == 'POST':
            session.delete(delete_query)
            try:
                session.commit()
                flash('DELETE SUCCESS!!: " %s " ...category deleted' % delete_query.category_name)
                return redirect(url_for('show_categories'))
            except SQLAlchemyError as _:
                flash('DELETE EXCEPTION OCCURRED!!: Delete Failed. Something went wrong when deleting category')
                return redirect(url_for('show_categories'))
            finally:
                session.close() 
        else:
            return render_template('deletecategory.html', category=delete_query, items=items)
    else:
        flash('LOGIN!!: Feature requires login. Please log in. You are redirected to the home page...')
        return redirect(url_for('home'))

# **** END CATEGORY ****


# **** START ITEMS ****
# Show all items
@app.route('/items/')
def show_all_items():
    
        items = session.query(Items).order_by(asc(Items.item_name))
        print(items)
        return render_template('items.html', items=items)


# Show all items in Category
@app.route('/category/<int:category_id>/items/')
def show_category_items(category_id):
    category = session.query(Category).filter_by(category_id=category_id).one()
    items = session.query(Items).filter_by(category_id=category_id).all()
    return render_template('categoryitems.html', items=items, category=category)


# Add new item for a Category
@app.route('/category/<int:category_id>/new', methods=['GET', 'POST'])
def add_new_item_for_category(category_id):
    login_status = loginstatus()
    if login_status is True:
        category = session.query(Category).filter_by(category_id=category_id).one()
        
        if request.method == 'POST':
            new_item = Item(item_name=request.form['name'], item_description=request.form['description'],
                            category_id=category_id, user_id=login_session['user_id'])
            session.add(new_item)
            try:
                session.commit()
                flash('CREATE SUCCESS!!: " %s " ...new item added to category' % new_item.item_name)
                return redirect(url_for('show_category_items', category_id=category.category_id))
            except SQLAlchemyError as _:
                flash('CREATE EXCEPTION OCCURRED!!: Failed to add new item. Something went wrong when adding new item.')
                return redirect(url_for('show_category_items', category_id=category.category_id))
            finally:
                session.close()
        else:
            return render_template('newitem.html', category=category)
    else:
        flash('LOGIN!!: Feature requires login. Please log in. You are redirected to the home page...')
        return redirect(url_for('home'))


# Edit item in a Category
# @app.route('/items/edit')
@app.route('/category/<int:category_id>/items/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item_in_category(category_id, item_id):
    login_status = loginstatus()
    if login_status is True:
        edit_item = session.query(Items).filter_by(item_id=item_id).one()
        category = session.query(Category).filter_by(category_id=category_id).one()
        
        if edit_item.user_id != login_session['user_id']:
            flash('EDIT NOT ALLOWED!!: " %s " ...creator alone has permission to edit' % edit_item.item_name)
            return redirect(url_for('show_category_items', category_id=category.category_id))

        if request.method == 'POST':
            if request.form['name']:
                edit_item.item_name = request.form['name']
                edit_item.item_description = request.form['description']
                session.add(edit_item)
                try:
                    session.commit()
                    flash('EDIT SUCCESS!!: " %s " ...item name modified' % edit_item.item_name)
                    return redirect(url_for('show_category_items', category_id=category.category_id))
                except SQLAlchemyError as _:
                    flash('EDIT EXCEPTION OCCURRED!!: Edit Failed. Something went wrong when saving changes')
                    return redirect(url_for('show_category_items', category_id=category.category_id))
                finally:
                    session.close()
        else:
            return render_template('edititem.html', item=edit_item, category=category)
    else:
        flash('LOGIN!!: Feature requires login. Please log in. You are redirected to the home page...')
        return redirect(url_for('home'))
   

# Delete item in a Category
@app.route('/category/<int:category_id>/items/<int:item_id>/delete', methods=['GET', 'POST'])
def delete_item_in_category(category_id, item_id):
    login_status = loginstatus()
    if login_status is True:
        delete_item = session.query(Items).filter_by(item_id=item_id).one()
        category = session.query(Category).filter_by(category_id=category_id).one()
        
        if delete_item.user_id != login_session['user_id']:
            flash('DELETE NOT ALLOWED!!: " %s " ...creator alone has permission to edit' % delete_item.item_name)
            return redirect(url_for('show_category_items', category_id=category.category_id))

        if request.method == 'POST':
            
            session.delete(delete_item)
            try:
                session.commit()
                flash('DELETE SUCCESS!!: " %s " ...item name deleted' % delete_item.item_name)
                return redirect(url_for('show_category_items', category_id=category.category_id))
            except SQLAlchemyError as _:
                flash('DELETE EXCEPTION OCCURRED!!: Delete Failed. Something went wrong when deleting item')
                return redirect(url_for('show_category_items', category_id=category.category_id))
            finally:
                session.close()
        else:
            return render_template('deleteitem.html', item=delete_item, category=category)
    else:
        flash('LOGIN!!: Feature requires login. Please log in. You are redirected to the home page...')
        return redirect(url_for('home'))


# **** END ITEMS ****


# JSON API End Points 

# Show all categories
@app.route('/categories/JSON')
def show_categories_json():
    try:
        categories = (session.query(Category).order_by(Category.category_name).all())
        return jsonify(Categories=[c.serialize for c in categories])
    except SQLAlchemyError as _:
        return "JSON EXCEPTION: showCategoriesJSON "


# Show details of a specific category
@app.route('/categorydetails/<int:category_id>/JSON')
def category_details_json(category_id):
    try:
        category = session.query(Category).filter_by(category_id=category_id).one()
        return jsonify(CategoryDetails=category.serialize)
    except SQLAlchemyError as _:
        return "JSON EXCEPTION: categoryDetailsJSON "


@app.route('/recentitems/JSON')
def show_recent_items_json():
    try:
        recent_items_added\
            = (session.query(Items).order_by(Items.item_id.desc()).limit(10))
        return jsonify(RecentItems=[c.serialize for c in recent_items_added])
    except SQLAlchemyError as _:
        return "JSON EXCEPTION: showrecentItems "


# Show all items in Category
@app.route('/category/<int:category_id>/items/JSON')
def show_items_in_category_json(category_id):
    try:
        items = session.query(Items).filter_by(category_id=category_id).all()
        return jsonify(CategoryItems=[i.serialize for i in items])
    except SQLAlchemyError as _:
        return "JSON EXCEPTION: showItemsInCategory "

# Show details of specific item in a Category
@app.route('/items/<int:item_id>/JSON')
def show_item_details_json(item_id):
    try:
        item = session.query(Items).filter_by(item_id=item_id).one()
        return jsonify(ItemDetails=item.serialize)
    except SQLAlchemyError as _:
        return "JSON EXCEPTION: showItemsInCategory "

# END API End Points


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
    # app.run()
