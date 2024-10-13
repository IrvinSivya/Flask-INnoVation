import os
import folium

from flask import Flask,render_template,request,flash,redirect
from flask_login import current_user,login_user,logout_user,UserMixin,LoginManager,login_required
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB

app = Flask(__name__)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

#engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost:5432/InnovativeHacksUsers")

#Configuring the flask app to have a PostgresSQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:postgres@localhost:5432/InnovativeHacksUsers'
app.config['SECRET_KEY'] = 'wkhfwyufge671f8ouhewfvyft'

db = SQLAlchemy(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    hashed_password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    skills = db.relationship('Skill', backref='users', lazy=True)

    #Overriding get_id since the id is named "user_id" instead of "id"
    def get_id(self):
        return str(self.id)

class Skill(db.Model):
    __tablename__ = "skills"
    id = db.Column(db.Integer, primary_key=True)
    skills = db.Column(JSONB, default=list)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 

#Creates the table
with app.app_context():
    db.create_all()

#Main page when not logged in
@app.route("/")
def index():
    return render_template("index.html")

#Main page after logged in
@app.route("/main", methods = ["GET","POST"])
def main():
    return render_template("main.html")

#SignUp class
class signUp():
    #Sign up page
    @app.route("/signUp", methods = ["POST"])
    def signUp():
        return render_template("signUp.html")

    #Adds the user to the database
    @app.route("/addUser", methods = ["POST"])
    def addUser():
        fName = request.form.get("firstName")
        lName = request.form.get("lastName")
        email = request.form.get("email")
        password = request.form.get("password")

        #Checks if email is already in use
        if User.query.filter_by(email=email).first():
            return render_template("error.html", loggedIn=False, message="Email already in use")

        #Creates the hashed password
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(first_name = fName, last_name = lName, email = email, hashed_password = password_hash)
        db.session.add(new_user)
        db.session.commit()

        return render_template("login.html")

#Login class
class Login():
    #Login page
    @app.route("/login", methods = ["POST"])
    def login():
        return render_template("login.html")

    #Checks whether login is valid or not
    @app.route("/verifyLogin", methods = ["POST"])
    def verifyLogin():
        email = request.form.get("email")
        password = request.form.get("password")

        #Checks if the email exists
        if db.session.query(User).filter_by(email=email).first() is None:
            return render_template("error.html",loggedIn=False, message = "Invalid password or email")
 
        #Gets the hashed password and name of the user based on the email they entered
        user = User.query.filter_by(email=email).first()
        hashed_password = user.hashed_password
        name = user.first_name
        
        if bcrypt.check_password_hash(hashed_password, password):
            login_user(user)
            return render_template("main.html",message = "Welcome back")
        else:
            return render_template("error.html",loggedIn=False, message = "Invalid password or email")  

#Logout class
class Logout():
    #Logs the user out
    @app.route("/logout", methods = ["GET","POST"])
    def logout():
        logout_user()
        return render_template("index.html")  

class ViewUsers():
    #View users page (this if for testing purposes only)
    @app.route("/viewUsers", methods = ["POST"])
    def viewUsers():
        users = User.query.all()
        return render_template("viewUsers.html",users=users)

class skills():
    @app.route("/skillOptions", methods = ["GET","POST"])
    @login_required
    def skillOptions():
        return render_template("skillOptions.html")

    #Adds the skill to the database
    @app.route("/addSkill", methods = ["GET","POST"])
    @login_required
    def addSkill():
        user_id = current_user.id
        #gets user and their skills
        user = User.query.get(user_id) #Gets the user
        user_skills = Skill.query.filter(Skill.user_id == user.id).all() #Gets all the Skill objects 

        current_skills = []
        for skill in user_skills:
            current_skills.append(skill.skills)
      
        subject_skill_name = request.form.get('subject') #Gets the name of the skill
        subject_skill = Skill(skills=subject_skill_name, user_id = user.id) #Creates an instance of Skill

        if not user_skills:
            user.skills = []
        
        if subject_skill_name in current_skills:
            return render_template("error.html", loggedIn = True, message="You already got this skill")

        user.skills.append(subject_skill)

        try:
            db.session.commit()     
            db.session.refresh(user)
        except Exception as e:
            db.session.rollback()
            print("Error during commit:", str(e))
            return {"error": "Failed to add skill" + str(e)}, 500
                
        return render_template("main.html")

class Tutor():
    #Displays users with a skill
    @app.route("/getTutors", methods = ["GET","POST"])
    @login_required
    def getTutors():
        # Query to get users with skills
        usersWithSkills = db.session.query(User).join(Skill).all()
        return render_template("displayTutors.html",usersWithSkills=usersWithSkills)

    @app.route("/searchTutors", methods = ["GET","POST"])
    @login_required
    def searchTutors():
        skill_name = request.args.get('skill_searched','').lower()

        usersWithSkills = db.session.query(User).join(Skill).all()

        usersWithSpecifiedSkill = []

        for user in usersWithSkills:
            for skill in user.skills:
                if(skill_name in skill.skills):
                    usersWithSpecifiedSkill.append(user)
                                  
        for user in usersWithSpecifiedSkill:
            print("USER WITH SKILL USER WITH SKILL USER WITH SKILL:   " + user.first_name)

        return render_template("searchedTutors.html",usersWithSpecifiedSkill=usersWithSpecifiedSkill)


#Runs the program
if __name__ == "__main__":
    app.run(debug=True)