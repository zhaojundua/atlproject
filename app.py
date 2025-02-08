from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from datetime import date, datetime, timedelta
import mysql.connector
import mysql.connector.pooling
import connect

app = Flask(__name__)

dbconn = None
connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="atl",
    user=connect.dbuser,
    password=connect.dbpass,
    host=connect.dbhost,
    database=connect.dbname,
    autocommit=True
)
connection = None

def getCursor():
    global dbconn
    global connection
    if connection is None:
        connection = connection_pool.get_connection()
    if dbconn is None:
        dbconn = connection.cursor(dictionary=True)
    return dbconn

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/tours", methods=["GET", "POST"])
def tours():
    cursor = getCursor()
    if request.method == "GET":
        qstr = "SELECT tourid, tourname FROM tours;" 
        cursor.execute(qstr)        
        tours = cursor.fetchall()    
        return render_template("tours.html", tours=tours)
    else:
        tourid = request.form.get("tourid")      
        qstr = "SELECT tourgroupid, startdate FROM tourgroups WHERE tourid=%s;" 
        cursor.execute(qstr, (tourid,))        
        tourgroups = cursor.fetchall()  
        return render_template("tours.html", tourid=tourid, tourgroups=tourgroups)
    
@app.route("/tours/list", methods=["POST"])
def tourlist():
  
    tourgroupid = request.form.get('tourgroupid')
    cursor = getCursor()

    qstr = """
        SELECT c.customerid, c.firstname, c.familyname, c.email, c.phone
        FROM customers c
        JOIN tourbookings tb ON c.customerid = tb.customerid
        WHERE tb.tourgroupid = %s;
    """
    cursor.execute(qstr, (tourgroupid,))
    customerlist = cursor.fetchall()

    if not customerlist:
        return f"No customers found for tour group ID {tourgroupid}.", 404

    return render_template("tourlist.html", customerlist=customerlist)


@app.route("/customers")
def customers():
    # List customer details
    cursor = getCursor()
    query = "SELECT customerid, firstname, familyname, dob, email, phone FROM customers;"
    cursor.execute(query)
    customers_data = cursor.fetchall()
    return render_template("customers.html", customers=customers_data)


@app.route("/customers/search", methods=["POST"])
def search_customers():
    cursor = getCursor()
    keyword = request.form.get('keyword')
    query = """
        SELECT customerid, firstname, familyname, dob, email, phone
        FROM customers
        WHERE firstname LIKE %s OR familyname LIKE %s OR email LIKE %s;
    """
    search_term = f"%{keyword}%"
    cursor.execute(query, (search_term, search_term, search_term))
    search_results = cursor.fetchall()
    return render_template("customers.html", customers=search_results)


@app.route("/customers/add", methods=["GET", "POST"])
def add_customer():
    cursor = getCursor()
    if request.method == "POST":
        firstname = request.form.get("firstname")
        familyname = request.form.get("familyname")
        dob = request.form.get("dob")
        email = request.form.get("email")
        phone = request.form.get("phone")
        query = """
            INSERT INTO customers (firstname, familyname, dob, email, phone)
            VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(query, (firstname, familyname, dob, email, phone))
        connection.commit()
        return redirect(url_for("customers"))
    return render_template("add_customer.html")

@app.route("/customers/edit/<int:customerid>", methods=["GET", "POST"])
def edit_customer(customerid):
    cursor = getCursor()
    if request.method == "POST":
        firstname = request.form.get("firstname")
        familyname = request.form.get("familyname")
        dob = request.form.get("dob")
        email = request.form.get("email")
        phone = request.form.get("phone")
        query = """
            UPDATE customers
            SET firstname=%s, familyname=%s, dob=%s, email=%s, phone=%s
            WHERE customerid=%s;
        """
        cursor.execute(query, (firstname, familyname, dob, email, phone, customerid))
        connection.commit()
        return redirect(url_for("customers"))
    query = "SELECT * FROM customers WHERE customerid=%s;"
    cursor.execute(query, (customerid,))
    customer = cursor.fetchone()
    return render_template("edit_customer.html", customer=customer)


@app.route("/booking/add", methods=["GET", "POST"])
def makebooking():
    cursor = getCursor()
    if request.method == "POST":
    
        tourgroupid = request.form.get("tourgroupid")
        customerid = request.form.get("customerid")
        booking_date = request.form.get("booking_date")
        
        query = """
            INSERT INTO tourbookings (tourgroupid, customerid, booking_date)
            VALUES (%s, %s, %s);
        """
        cursor.execute(query, (tourgroupid, customerid, booking_date))
        connection.commit()
        
        return redirect(url_for("tourlist", tourgroupid=tourgroupid))

    qstr_tours = "SELECT tourgroupid, startdate FROM tourgroups;"
    cursor.execute(qstr_tours)
    tourgroups = cursor.fetchall()

    qstr_customers = "SELECT customerid, firstname, familyname FROM customers;"
    cursor.execute(qstr_customers)
    customers = cursor.fetchall()

    return render_template("add_booking.html", tourgroups=tourgroups, customers=customers)



if __name__ == "__main__":
    app.run(debug=True)
