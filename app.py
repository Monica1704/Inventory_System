from flask import Flask,render_template,url_for,redirect,request,flash
from flask_mysqldb import MySQL
app=Flask(__name__)
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]="sumathimurugan@17"
app.config["MYSQL_DB"]="inventorysystem"
app.config["MYSQL_CURSORCLASS"]="DictCursor"
mysql=MySQL(app)
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/location")
def location():
    con=mysql.connection.cursor()
    sql="SELECT * FROM Location"
    con.execute(sql)
    res=con.fetchall()
    return render_template("location.html",datas=res)
@app.route("/product")
def product():
    con=mysql.connection.cursor()
    sql="SELECT * FROM Products"
    con.execute(sql)
    res=con.fetchall()
    return render_template("product.html",datas=res)

@app.route("/addproduct",methods=['GET','POST'])
@app.route("/addproduct", methods=['GET', 'POST'])
def addproduct():
    if request.method == 'POST':
        name = request.form['Name']
        try:
            price = float(request.form['Price'])
            quantity = int(request.form['Quantity'])

            if price < 0 or quantity < 0:
                flash("Price and Quantity must be non-negative.")
                return redirect(url_for("addproduct"))

            con = mysql.connection.cursor()
            sql = "INSERT INTO Products(Name, Price, Quantity) VALUES (%s, %s, %s)"
            con.execute(sql, [name, price, quantity])
            mysql.connection.commit()
            con.close()
            return redirect(url_for("home"))

        except ValueError:
            flash("Invalid input: Price must be a number, Quantity must be an integer.")
            return redirect(url_for("addproduct"))

    return render_template("addproduct.html")

@app.route("/addlocation",methods=['GET','POST'])
def addlocation():
    if request.method=='POST':
        name=request.form['LocationName']
        con=mysql.connection.cursor()
        sql="insert into Location(LocationName) value(%s)"
        con.execute(sql,[name])  
        mysql.connection.commit()
        con.close()
       
        return redirect(url_for("home"))
    return render_template("addlocation.html");
@app.route("/editproduct/<string:id>",methods=['GET','POST','PUT'])
def editproduct(id):
    
    con=mysql.connection.cursor()
    if request.method=='POST':
        name=request.form['Name']
        price=request.form['Price']
        quantity=request.form['Quantity'] 
        con=mysql.connection.cursor()
        sql="UPDATE Products SET Name=%s, Price=%s, Quantity=%s WHERE ProductID=%s"

        con.execute(sql,[name,price,quantity,id])  
        mysql.connection.commit()
        con.close()
        return redirect(url_for("home"))
    sql="select * from Products where ProductID=%s"
    con.execute(sql,[id])
    res=con.fetchone()
    return render_template('editproduct.html',datas=res)
@app.route("/editlocation/<string:id>",methods=['GET','POST'])
def editlocation(id):
    con=mysql.connection.cursor()
    if request.method=='POST':
        name=request.form['LocationName'] 
        con=mysql.connection.cursor()
        sql="UPDATE Location SET LocationName=%s WHERE LocationID=%s"

        con.execute(sql,[name,id])  
        mysql.connection.commit()
        con.close()
        return redirect(url_for("home"))
    sql="select * from Location where LocationID=%s"
    con.execute(sql,[id])
    res=con.fetchone()
    return render_template('editlocation.html',datas=res)
@app.route("/addmovement", methods=["GET", "POST"])
def addmovement():
    cur = mysql.connection.cursor()

    if request.method == "POST":
        product_id = request.form['ProductID']
        from_location = request.form.get('FromLocationID') or None
        to_location = request.form.get('ToLocationID') or None
        quantity = int(request.form['Quantity'])
        cur.execute("SELECT Quantity FROM Products WHERE ProductID = %s", [product_id])
        result = cur.fetchone()

        if result is None:
            return "Product not found", 400

        available_qty = result['Quantity']
        if quantity > available_qty:
            return f"Insufficient quantity. Available: {available_qty}", 400
        sql = """
        INSERT INTO ProductMovement (ProductID, FromLocationID, ToLocationID, Quantity)
        VALUES (%s, %s, %s, %s)
        """
        cur.execute(sql, [product_id, from_location, to_location, quantity])

        cur.execute("UPDATE Products SET Quantity = Quantity - %s WHERE ProductID = %s", [quantity, product_id])

        if from_location:
            cur.execute("""
                INSERT INTO ProductBalance (LocationID, ProductID, Quantity)
                VALUES (%s, %s, -%s)
                ON DUPLICATE KEY UPDATE Quantity = Quantity - %s
            """, (from_location, product_id, quantity, quantity))
        if to_location:
            cur.execute("""
                INSERT INTO ProductBalance (LocationID, ProductID, Quantity)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE Quantity = Quantity + %s
            """, (to_location, product_id, quantity, quantity))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for("home"))
    cur.execute("SELECT * FROM Products")
    products = cur.fetchall()
    cur.execute("SELECT * FROM Location")
    locations = cur.fetchall()
    cur.close()
    return render_template("addmovement.html", products=products, locations=locations)


@app.route("/movements")
def movements():
    cur = mysql.connection.cursor()

    sql = """
    SELECT 
        pm.MovementID,
        p.ProductID,
        p.Name AS ProductName,
        fl.LocationName AS FromLocation,
        tl.LocationName AS ToLocation,
        pm.Quantity
    FROM ProductMovement pm
    JOIN Products p ON pm.ProductID = p.ProductID
    LEFT JOIN Location fl ON pm.FromLocationID = fl.LocationID
    LEFT JOIN Location tl ON pm.ToLocationID = tl.LocationID
    ORDER BY pm.MovementID DESC
    """

    cur.execute(sql)
    movements = cur.fetchall()
    cur.close()

    return render_template("view_movements.html", movements=movements)

@app.route("/report")
def report():
    cur = mysql.connection.cursor()
    sql = """
    SELECT pb.LocationID, l.LocationName, pb.ProductID, p.Name AS ProductName, pb.Quantity
    FROM ProductBalance pb
    JOIN Location l ON pb.LocationID = l.LocationID
    JOIN Products p ON pb.ProductID = p.ProductID
    ORDER BY pb.LocationID, pb.ProductID
    """
    cur.execute(sql)
    data = cur.fetchall()
    cur.close()
    return render_template("report.html", report=data)

if(__name__=='__main__'):
    app.secret_key="abc123"
    app.run(debug=True)
