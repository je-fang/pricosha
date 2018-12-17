#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors, datetime

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       #port = 8889,
                       user='root',
                       password='',
                       db='pricosha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE email = %s and password = %s'
    cursor.execute(query, (username, password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None

    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    firstname = request.form['firstname']
    lastname = request.form['lastname']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE email = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None

    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (username, password, firstname, lastname))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    return render_template('home.html')

#Define route for login
@app.route('/post')
def post():
    return render_template('post.html')

@app.route('/makepost', methods=['GET', 'POST'])
def makepost():
    username = session['username']
    cursor = conn.cursor();
    posttime = datetime.datetime.now().strftime('%y-%m-%d %H:%M:%S')
    puborpriv = request.form['puborpriv']
    filepath = request.form['filepath']
    itemname = request.form['itemname']

    query = 'INSERT INTO contentitem (email_post, post_time, file_path, item_name, is_pub) ' \
            'VALUES(%s, %s, %s, %s, %s)'
    cursor.execute(query, (username, posttime, filepath, itemname, puborpriv))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

#Define route for login
@app.route('/dashboard', methods=["GET", "POST"])
def dashboard():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM contentitem AS c ' \
            'WHERE c.is_pub = 1 OR c.email_post = %s ' \
            'OR c.item_id IN (SELECT s.item_id ' \
            'FROM share AS s NATURAL JOIN belong AS b NATURAL JOIN friendgroup AS f ' \
            'WHERE b.email = %s)'

    cursor.execute(query, (username, username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('dashboard.html', username=username, posts=data)

@app.route('/details', methods = ["GET", "POST"])
def details():
    username = session['username']
    itemid = request.args.get('itemid')

    cursor = conn.cursor();
    query = 'SELECT count(*) AS num FROM rate WHERE emoji = ":-)"'
    cursor.execute(query)
    numratings = cursor.fetchone()
    cursor.close()

    cursor = conn.cursor();
    query2 = 'SELECT fname, lname FROM person NATURAL JOIN tag NATURAL JOIN contentitem AS c ' \
             'WHERE c.item_id = %s'
    cursor.execute(query2, (int(itemid)))
    persondata = cursor.fetchall()
    cursor.close()

    return render_template('details.html', username=username, posts=persondata, ratings=numratings)

@app.route('/managetags', methods = ["GET", "POST"])
def managetags():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT DISTINCT * FROM person as p NATURAL JOIN tag AS t NATURAL JOIN contentitem AS c ' \
             'WHERE t.status = "false" AND t.email_tagged = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()

    return render_template('managetags.html', username=username, posts=data)

@app.route('/accepttag', methods = ["GET", "POST"])
def accepttag():
    itemid = request.args.get('itemid')
    username = session['username']
    cursor = conn.cursor()
    upd = 'UPDATE tag SET status = "true" WHERE item_id = %s'
    cursor.execute(upd, (int(itemid)))
    cursor.close()

    return redirect(url_for('managetags'))

@app.route('/tag')
def tag():
    return render_template('tag.html')

@app.route('/tagperson', methods = ["GET", "POST"])
def tagperson():
    username = session['username']
    itemid = request.args.get('itemid')
    tagtime = datetime.datetime.now().strftime('%y-%m-%d %H:%M:%S')

    cursor = conn.cursor();
    taggee = request.form['taggee']
    ins = 'INSERT INTO tag(item_id, email_tagged, email_tagger, tagtime, status) VALUES (%s, %s, %s, %s, %s)'
    if (username == taggee):
        cursor.execute(ins, (int(itemid), username, username, tagtime, 'true'))
    else:
        cursor.execute(ins, (int(itemid), taggee, username, tagtime, 'false'))
    cursor.close()

    return redirect(url_for('dashboard'))

@app.route('/friend')
def friend():
    return render_template('friend.html')

@app.route('/addfriend', methods=['GET', 'POST'])
def addfriend():
    username = session['username']
    cursor = conn.cursor();
    fgname = request.form['fgname']
    friendfirst = request.form['friendfirst']
    friendlast = request.form['friendlast']

    query = 'SELECT email FROM person WHERE fname = %s AND lname = %s'
    cursor.execute(query, (friendfirst, friendlast))
    group = cursor.fetchone()
    femail = group["email"]
    cursor.close()

    cursor = conn.cursor()
    query2 = 'SELECT email FROM belong ' \
            'WHERE email = %s AND owner_email = %s AND fg_name = %s'
    cursor.execute(query2, (femail, username, fgname))
    ingroup = cursor.fetchall()
    cursor.close()

    if(ingroup):
        error = "This user is already in the group"
        return render_template('friend.html', error=error)
    else:
        cursor = conn.cursor()
        ins = 'INSERT INTO belong(email, owner_email, fg_name) VALUES(%s, %s, %s)'
        print("things", type(femail), femail, username, fgname)
        cursor.execute(ins, (femail, username, fgname))
        conn.commit()
        cursor.close()

        return redirect(url_for('home'))


@app.route('/select_blogger')
def select_blogger():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    
    cursor = conn.cursor();
    query = 'SELECT DISTINCT email FROM person'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_blogger.html', user_list=data)

@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    cursor = conn.cursor();
    query = 'SELECT post_time, item_name FROM contentitem WHERE email = %s ORDER BY post_time DESC'
    cursor.execute(query, poster)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_posts.html', poster_name=poster, posts=data)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
