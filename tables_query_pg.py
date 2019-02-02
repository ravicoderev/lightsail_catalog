#! Python 3.4
# "Sporting Goods Catalog"

import datetime
import psycopg2
import bleach
import csv

DBNAME = "sportscatalogitems"



# TABLE - 1. users


def users():
    db = psycopg2.connect(user="sportscatalogitems", password="1234", host="localhost", port="5432", database=DBNAME)
    c = db.cursor()
    q1 = "select * from users"
    
    select_query = q1 
    c.execute(select_query)
    results = c.fetchall()
    print(results)
    #  return reversed(results) # write into text file
    with open('users.txt', 'w') as f:
        #  writer = csv.writer(f, delimiter=',')
        for row in results:
            # writer.writerow(row)
            f.write("%s\n" % str(row))
    print("Done Writing")
    db.close()


# TABLE - 2. category


def category():
    db = psycopg2.connect(user="sportscatalogitems", password="1234", host="localhost", port="5432", database=DBNAME)
    c = db.cursor()
    q1 = "select * from category"
    
    select_query = q1 
    c.execute(select_query)
    results = c.fetchall()
    print(results)
    #  return reversed(results) # write into text file
    with open('category.txt', 'w') as f:
        #  writer = csv.writer(f, delimiter=',')
        for row in results:
            # writer.writerow(row)
            f.write("%s\n" % str(row))
    print("Done Writing")
    db.close()


# TABLE - 3. items


def items():
    db = psycopg2.connect(user="sportscatalogitems", password="1234", host="localhost", port="5432", database=DBNAME)
    c = db.cursor()
    q1 = "select * from items"
    
    select_query = q1 
    c.execute(select_query)
    results = c.fetchall()
    print(results)
    #  return reversed(results) # write into text file
    with open('items.txt', 'w') as f:
        #  writer = csv.writer(f, delimiter=',')
        for row in results:
            # writer.writerow(row)
            f.write("%s\n" % str(row))
    print("Done Writing")
    db.close()


users()
category()
items()