from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from werkzeug.security import generate_password_hash, check_password_hash

from helpers import *
# объявление структуры
class Question:
    def __init__(self, text):
        self.text = text
        self.answers = list()
        self.idx_true = -1


# configure application
app = Flask(__name__)


# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response


# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# configure CS50 Library to use SQLite database
db = SQL("sqlite:///final_project.db")
@app.route("/")
@login_required
def index():
    return redirect(url_for("test"))

@app.route("/form", methods=["GET", "POST"])
@login_required
def form():

    if request.method == "GET":
        return render_template("form.html")

    else:
        _test_id = db.execute("SELECT * FROM testname WHERE test IS :test", test=request.form.get("testname"))

        if not _test_id:

            # добавляем новое имя теста в базу данных
            db.execute("INSERT INTO testname (test) VALUES(:test)", test=request.form.get("testname"))

            # получаем id и имя нового теста
            _test_id = db.execute("SELECT * FROM testname WHERE test IS :test", test=request.form.get("testname"))

        # Вставка вопроса
        radio_id = request.form['optionsRadios'] # чекнутый радиобатон

        db.execute("INSERT INTO question (quest_text, test_id, ok_answer) VALUES(:quest_text, :test_id, :ok_answer)",
                    quest_text=request.form.get("question"), test_id = _test_id[0]["idtest"], ok_answer=radio_id)

        # Получение id вопроса
        q_id = db.execute("SELECT id FROM question WHERE quest_text IS :quest_text", quest_text=request.form.get("question"))

        # Вставка ответа
        answer = request.form.get("answer1")
        if answer != '':
            db.execute("INSERT INTO answer (id, answertext) VALUES(:id, :answertext)",
                id = q_id[0]['id'], answertext = answer)

        answer2 = request.form.get("answer2")
        if answer2 != '':
            db.execute("INSERT INTO answer (id, answertext) VALUES(:id, :answertext)", id=q_id[0]['id'], answertext = answer2)
        else:
            return apology("Fill in all the fields")

        answer3 = request.form.get("answer3")
        if answer3 != '':
            db.execute("INSERT INTO answer (id, answertext) VALUES(:id, :answertext)", id=q_id[0]['id'], answertext = answer3)

        answer4 = request.form.get("answer4")
        if answer4 != '':
            db.execute("INSERT INTO answer (id, answertext) VALUES(:id, :answertext)", id=q_id[0]['id'], answertext = answer4)

        # Кнопка создать новый тест
        if request.form.get('btn', None) == "new_test":
            return redirect(url_for("test", _idtest=_test_id[0]['idtest']))
        else:
            # кнопка добавить вопрос
            if request.form.get('btn', None) == "new_question":
                return render_template("form.html", _nametest=_test_id[0]['test']) # _nametest передаётся в HTML



@app.route("/ChooseTest", methods=["GET", "POST"])
@login_required
def ChooseTest():
    if request.method == "GET":
        tests = db.execute("SELECT * FROM testname WHERE test IS NOT NULL")
        return render_template("ChooseTest.html", _tests = tests)

    else:
        return redirect(url_for("test", _idtest = request.form.get('tests', None)))



@app.route("/test", methods=["GET", "POST"])
@login_required
def test():
    try:
        if request.method == "POST":
            return apology("Opps!!!")

        else:
            try:
                id_test = request.args["_idtest"] # при переходе на страничку в аргументе передаётся id теста
            except Exception  as err:
                print("Exception here")

            # Получаем имя теста
            nametest = db.execute("SELECT test FROM testname WHERE idtest=:idtest", idtest = id_test)

            # Получаем все вопросы указанного теста
            questions = db.execute("SELECT * FROM question WHERE test_id=:test_id", test_id = id_test)

            if not questions:
                return apology("No questions found for current test")

            # Объявляем пустой список вопросов
            my_questions = list()

            # Перебор всех вопросов из запроса и заполнение списка вопросов
            for i in range(len(questions)):
                my_question = Question(questions[i]["quest_text"]) # создаем экземпляр класса и передаем текст вопроса

                # полю idx_true класса присваиваем номер правильного ответа из БД
                my_question.idx_true = questions[i]["ok_answer"]

                # Запрос ответов для текущего вопроса
                answers = db.execute("SELECT * FROM answer WHERE id=:id", id = questions[i]["id"])

                if not answers:
                    apology("No answers found for current question")

                # Все ответы заносятся в список ответов данного вопроса
                for k in range(len(answers)):
                    my_question.answers.append(answers[k]["answertext"])

                my_questions.append(my_question);

            return render_template("test.html", _nametest = nametest[0]["test"], _questions = my_questions)

    except Exception  as err:
        return apology("Exception: {0}".format(err))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for symbol
        rows = db.execute("SELECT * FROM users WHERE username IS :username",
                          username=request.form.get("username"))

        # ensure username exists and password is correct
        pass_check = check_password_hash(rows[0]["hash"], request.form.get("password"))

        if len(rows) != 1 or not pass_check:
             return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("form"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password")

        elif not request.form.get("confirmation"):
            return apology("must confirm password")

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match")

        # добавляем нового пользователя в базу данных по хеш-паролю
        result = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=request.form.get(
            "username"), hash=generate_password_hash(request.form.get("password")))

        if not result:
            return apology("such username already exist")

        # store their id in session to log them in automatically
        user_id = db.execute("SELECT id FROM users WHERE username IS :username",
                             username=request.form.get("username"))

        session['user_id'] = user_id[0]['id']

        # redirect user to home page
        return redirect(url_for("form"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")




