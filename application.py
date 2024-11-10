import os
import folium

from flask import Flask,render_template,request,flash,redirect,url_for
from flask_login import current_user,login_user,logout_user,UserMixin,LoginManager,login_required
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

from werkzeug.utils import secure_filename

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

#Configuring upload folder and profile pic extensions
UPLOAD_FOLDER = 'static/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

db = SQLAlchemy(app)

#Ensures the uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
    profile_picture  = db.Column(db.String(1000))
    about_me = db.Column(db.String(500))
    phone_number = db.Column(db.String(15), unique=True)

    skills = db.relationship('Skill', backref='users', lazy=True)
    achievements = db.relationship('Achievements', backref='users', lazy=True)

    #Overriding get_id since the id is named "user_id" instead of "id"
    def get_id(self):
        return str(self.id)

class Skill(db.Model):
    __tablename__ = "skills"
    id = db.Column(db.Integer, primary_key=True)
    skills = db.Column(JSONB, default=list)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 

class Achievements(db.Model):
    __tablename__ = "achievements"
    id = db.Column(db.Integer, primary_key=True)
    achievement = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 

#Creates the table
with app.app_context():
    db.create_all()

#Main page when not logged in
@app.route("/")
def index():
    return render_template("login.html")

#Main page after logged in
@app.route("/main", methods = ["GET","POST"])
def main():
    return render_template("main.html")

#SignUp class
class signUp():
    #Sign up page
    @app.route("/signUp", methods = ["POST","GET"])
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
        return render_template("login.html")  

class ViewUsers():
    #View users page (this if for testing purposes only)
    @app.route("/viewUsers", methods = ["POST"])
    def viewUsers():
        users = User.query.all()
        return render_template("viewUsers.html",users=users)

class Skills():
    @app.route("/userSkills", methods = ["GET","POST"])
    @login_required
    def userSkills():
        user_id = current_user.id
        #gets user and their skills
        user = User.query.get(user_id) #Gets the user
        user_skills = Skill.query.filter(Skill.user_id == user.id).all() #Gets all the Skill objects 

        current_skills = []
        for skill in user_skills:
            current_skills.append(skill.skills)

        return render_template("userSkills.html", current_skills=current_skills)  

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

class Profile():
    #Checks if the picture's extension is allowed
    def allowed_file(filename):
        return 

    @app.route("/profile", methods = ["GET","POST"])
    @login_required
    def profile():
        user_id = current_user.id
        #gets user and their skills
        user = User.query.get(user_id) #Gets the user
        user_profile = user.profile_picture
        achievements = user.achievements
        if user_profile is None:
            user_profile="default.png"
    
        return render_template("profile.html",telephone_number = user.phone_number, about_me = user.about_me,isOthers=False,
        achievements=achievements,username = user.first_name, user_profile=user_profile)

    @app.route("/viewOthersProfile",methods = ["GET","POST"])
    @login_required
    def viewOthersProfile():
        user_id = request.args.get('user_id')
        user = User.query.get(user_id) #Gets the user
        user_profile = user.profile_picture
        achievements = user.achievements
        if user_profile is None:
            user_profile="default.png"
        return render_template("profile.html",telephone_number = user.phone_number, about_me = user.about_me,
        isOthers=True,achievements=achievements, username = user.first_name, user_profile=user_profile)
    
    @app.route("/uploadProfilePic", methods = ["GET","POST"])
    @login_required
    def uploadProfilePic():
        user_id = current_user.id
        user = User.query.get(user_id)

        if 'file' not in request.files:
            return redirect(url_for('profile'))

        file = request.files['file']

        allowed_file = '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
        
        if file and allowed_file:
            filename = secure_filename(file.filename)
            
            # Save the file in the upload folder
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            user.profile_picture = filename

            try:
                db.session.commit()     
                db.session.refresh(user)
            except Exception as e:
                db.session.rollback()
                print("Error during commit:", str(e))
                return {"error": "Failed to upload profile picture" + str(e)}, 500
            
            return redirect(url_for('profile'))

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

class UserAchievements():
    @app.route("/addAchievement", methods = ["GET","POST"])
    @login_required
    def addAchievement():
        user_id = current_user.id
        user = User.query.get(user_id)
        new_achievement_str = request.form.get('new_achievement')

        if(new_achievement_str is None):
            return render_template("error.html", message="New achievement is null")

        new_achievement = Achievements(achievement=new_achievement_str, user_id=user.id)
        user.achievements.append(new_achievement)

        try:
            db.session.commit()     
            db.session.refresh(user)
        except Exception as e:
            db.session.rollback()
            print("Error during commit:", str(e))
            return {"error": "Failed to add achievement" + str(e)}, 500
        return redirect(url_for('profile'))

class AboutMe():
    @app.route("/aboutMe", methods = ["GET","POST"])
    @login_required
    def aboutMe():
        user_id = current_user.id
        user = User.query.get(user_id)
        about_me = request.form.get('about_me')

        if(about_me is None):
            return render_template("error.html", message="About me is null")

        user.about_me = about_me

        try:
            db.session.commit()     
            db.session.refresh(user)
        except Exception as e:
            db.session.rollback()
            print("Error during commit:", str(e))
            return {"error": "Failed to add achievement" + str(e)}, 500
        return redirect(url_for('profile'))

class Telephone():
    @app.route("/telephoneNumber", methods = ["GET","POST"])
    @login_required
    def telephoneNumber():
        user_id = current_user.id
        user = User.query.get(user_id)
        telephone_number = request.form.get('telephone_number')

        if(telephone_number is None):
            return render_template("error.html", message="The Telephone number is null")

        user.phone_number = telephone_number

        try:
            db.session.commit()     
            db.session.refresh(user)
        except Exception as e:
            db.session.rollback()
            print("Error during commit:", str(e))
            return {"error": "Failed to add achievement" + str(e)}, 500
        return redirect(url_for('profile'))

#Runs the program
if __name__ == "__main__":
    app.run(debug=True)