import json
import os
import math
from werkzeug.utils import secure_filename
import mysql.connector as connection
from flask import Flask, render_template,request,session,redirect
from flask_mail import Mail

# Reading Json configuration file
with open("config.json","r") as c:
    params = json.load(c)["parameters"]

app = Flask(__name__)
app.secret_key ="super-secret-key"
app.config["UPLOAD_FOLDER"]= params["upload_location"]



# Setting Up Gmail configurations
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail_user"],
    MAIL_PASSWORD=params["gmail_password"]
)
mail = Mail(app)


# Rendering Home html template
@app.route("/")
def home():

    mydb = connection.connect(host=params["local_host"], user=params["user"], password=params["password"],
                              database=params["database"])
    cursor = mydb.cursor()
    value = [params["no_of_post"]]
    cursor.execute("SELECT * FROM posts")
    posts_in_table = cursor.fetchall()
    mydb.close()

    last = math.ceil(len(posts_in_table)/int(params["no_of_post"]))



    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)

    posts_in_table = posts_in_table[(page-1) * int(params["no_of_post"]):(page-1)*int(params["no_of_post"])+int(params["no_of_post"])]
    # pagination logic
    # First
    if (page==1):
        prev = "#"
        next = "/?page="+str(page+1)
    elif(page==last):
        prev = "/?page=" + str(page -1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, data=posts_in_table,prev=prev,next=next)


@app.route("/about")
def about():
    return render_template('about.html', params=params)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        mydb = connection.connect(host=params["local_host"], user=params["user"], password=params["password"],
                                  database=params["database"])
        cursor = mydb.cursor()
        cursor.execute("INSERT INTO contacts (name,email,phone,message) VALUES (%s,%s,%s,%s)",
                       (name, email, phone, message))
        mydb.commit()
        mydb.close()

        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[params["gmail_user"]],
                          body=message + "\n" + phone
                          )

    return render_template('contact.html', params=params)


@app.route("/post/<post_slug>", methods=['GET', 'POST'])
def post_route(post_slug):
    mydb = connection.connect(host=params["local_host"], user=params["user"], password=params["password"],
                              database=params["database"])
    cursor = mydb.cursor()
    value = [post_slug]
    print(value)
    cursor.execute("SELECT * FROM posts where slug = %s", value)
    posts_in_table = cursor.fetchall()
    mydb.close()
    return render_template('post.html', params=params, data=posts_in_table)


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user']==params['admin_user']):
        mydb = connection.connect(host=params["local_host"], user=params["user"], password=params["password"],
                                  database=params["database"])
        cursor = mydb.cursor()
        cursor.execute("Select * from posts")
        all_posts_data = cursor.fetchall()
        mydb.commit()
        mydb.close()
        return render_template('dashboard.html',params=params,posts=all_posts_data)

    if request.method == "POST":
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username==params["admin_user"] and userpass==params["admin_password"]):
            # set session variable
            session['user'] = username
            # get all posts from database
            mydb = connection.connect(host=params["local_host"], user=params["user"], password=params["password"],
                                      database=params["database"])
            cursor = mydb.cursor()
            cursor.execute("Select * from posts")
            all_posts_data=cursor.fetchall()
            mydb.commit()
            mydb.close()
            print(all_posts_data)
            return render_template('dashboard.html',params=params,posts=all_posts_data)
    return render_template("login.html", params=params)

@app.route("/edit/<sno>", methods=['GET', 'POST'])
def edit(sno):
    aa = []
    if ("user" in session and session["user"]==params['admin_user']):
        if request.method == 'POST':
            box_title   = request.form.get('title')
            tline       = request.form.get('tline')
            slug        = request.form.get('slug')
            content     = request.form.get('content')
            img         = request.form.get('img')

            if sno=="0":
                mydb = connection.connect(host=params["local_host"], user=params["user"], password=params["password"],
                                          database=params["database"])
                cursor = mydb.cursor()
                cursor.execute("INSERT INTO posts (title,tagline,content,images,slug) VALUES (%s,%s,%s,%s,%s)",
                               (box_title,tline,content,img,slug))
                mydb.commit()
                mydb.close()

    if ("user" in session and session["user"]==params['admin_user']):
        if request.method == 'POST':
            box_title   = request.form.get('title')
            tline       = request.form.get('tline')
            slug        = request.form.get('slug')
            content     = request.form.get('content')
            img         = request.form.get('img')
            mydb = connection.connect(host=params["local_host"], user=params["user"], password=params["password"],
                                      database=params["database"])
            print(sno)
            cursor = mydb.cursor()
            cursor.execute("UPDATE posts SET title=%s,tagline=%s,content=%s,images=%s,slug=%s WHERE Sno=%s",
                           (box_title, tline, content, img, slug, sno))
            aa=cursor.fetchall()
            print(aa)
            mydb.commit()
            mydb.close()

    return render_template('edit.html',params=params,sno=sno)

@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            f=request.files['file1']
            f.save(os.path.join(app.config["UPLOAD_FOLDER"],secure_filename(f.filename)))
            return  "Uploaded Succesfully"

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/delete/<sno>", methods=['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        mydb = connection.connect(host=params["local_host"], user=params["user"], password=params["password"],
                                  database=params["database"])
        print(sno)
        cursor = mydb.cursor()
        cursor.execute("DELETE FROM posts WHERE Sno=%s",[sno])
        mydb.commit()
        mydb.close()
    return redirect("/dashboard")

app.run(debug=True)
