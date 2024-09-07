from flask import Flask, render_template, request, url_for, redirect
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_ckeditor import CKEditor, CKEditorField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
from flask_login import LoginManager, current_user, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from sqlalchemy import desc
is_published = False

class Base(DeclarativeBase):
    pass


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///coursenet.db"
app.config['SECRET_KEY'] = 'some_secret_key'
bootstrap = Bootstrap5(app)
ckeditor = CKEditor()
ckeditor.init_app(app)
db = SQLAlchemy(model_class=Base)
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return UserDBModel.query.get_or_404(user_id)


class UserForm(FlaskForm):
    name = StringField(label='Name', validators=[DataRequired()],
                       render_kw={"placeholder": "Author name...", "class": "form-control"})
    email = StringField(label='Email', validators=[DataRequired()],
                        render_kw={"placeholder": "Email Address...", "class": "form-control"})
    password = PasswordField(label='Password', validators=[DataRequired()],
                             render_kw={"placeholder": "Password...", "class": "form-control"})
    submit = SubmitField(label='Proceed', render_kw={"class": "w-50 btn btn-outline-secondary btn-lg"})


class PostForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired()],
                        render_kw={"placeholder": "Enter title here...", "class": "form-control"})
    subtitle = StringField(label='Subtitle', validators=[DataRequired()],
                           render_kw={"placeholder": "Enter subtitle here...", "class": "form-control"})
    img_url = StringField(label='Img_URL', validators=[DataRequired()],
                          render_kw={"placeholder": "Enter image URL...", "class": "form-control"})
    content = CKEditorField(label='Content', validators=[DataRequired()],
                            render_kw={"placeholder": "Enter content...", "class": "form-control"})
    submit = SubmitField(label='Publish Post', render_kw={"class": "w-50 btn btn-outline-secondary btn-lg"})


class PostDBModel(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(nullable=False)
    author_name: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    subtitle: Mapped[str] = mapped_column(nullable=False)
    img_url: Mapped[str] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    date_published: Mapped[str] = mapped_column(nullable=False)


class UserDBModel(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)


with app.app_context():
    db.create_all()


@app.route('/login', methods=['POST', 'GET'])
def login():
    user_form = UserForm()
    if request.method == 'POST':
        if user_form.validate_on_submit:
            email = request.form.get('email')
            password = request.form.get('password')
            try:
                user = db.session.execute(db.select(UserDBModel).where(UserDBModel.email == email))
                user = user.scalar()

                if check_password_hash(user.password, password):
                    login_user(user)
                    return redirect(url_for('index'))
            except Exception as e:
                return f"{e}"

    
    return render_template('login.html', form=user_form)


@app.route('/register', methods=['POST', 'GET'])
def register():
    user_form = UserForm()
    if request.method == 'POST':
        if user_form.validate_on_submit():

            hashed_salt_password = generate_password_hash(password=request.form.get('password'), salt_length=8,
                                                          method='pbkdf2')
            new_user = UserDBModel(
                name = request.form.get('name'),
                email = request.form.get('email'),
                password = hashed_salt_password,
            )

            try:
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return redirect(url_for('index'))
            except Exception as e:
                return f"{e}"
    return render_template('register.html', form=user_form)


@app.route('/')
def index():
    entries = []
    try:
        entries = db.session.execute(db.select(PostDBModel).where(PostDBModel.author_id == current_user.id).order_by(desc(PostDBModel.date_published))).scalars().all()
    except Exception as e:
        return render_template('index.html', entries=entries)
    return render_template('index.html', entries=entries)


@app.route('/make-post', methods=['POST', 'GET'])
@login_required
def create_post():
    post_form = PostForm()
    if request.method == 'POST':
        if post_form.validate_on_submit():
            
            new_post = PostDBModel(
                author_id = int(current_user.id),
                author_name = str(current_user.name),
                title = request.form.get('title'),
                subtitle = request.form.get('subtitle'),
                img_url = request.form.get('img_url'),
                content = request.form.get('content'),
                date_published = datetime.datetime.now().strftime("%B %d %Y")
            )
            try:
                db.session.add(new_post)
                db.session.commit()

                return redirect(url_for('index'))
            except Exception as e:
                return f"{e}"
    return render_template('make-post.html', form=post_form)


@app.route('/community')
def community_page():
    try:
        entries = db.session.execute(db.select(PostDBModel).order_by(desc(PostDBModel.date_published))).scalars().all()
    except Exception as e:
        return f"{e}"
    return render_template('community.html', entries=entries)


@app.route('/post/<int:post_id>')
def post(post_id):
    entry = db.session.execute(db.select(PostDBModel).where(PostDBModel.id == post_id)).scalar()
    return render_template('post.html', entry=entry)


@app.route('/about')
def about():
    return render_template('about.html')



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
