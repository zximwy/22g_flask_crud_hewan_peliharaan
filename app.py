from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from forms import RegistrationForm, LoginForm, PetForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pets.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Owner(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    pets = db.relationship('Pet', backref='owner', lazy=True)

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(50))
    age = db.Column(db.Integer)
    weight = db.Column(db.Float)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return Owner.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_owner = Owner(name=form.name.data, email=form.email.data, password=form.password.data)
        db.session.add(new_owner)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        owner = Owner.query.filter_by(email=form.email.data).first()
        if owner and owner.password == form.password.data:  # Use hashed passwords in production
            login_user(owner)
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        user = User.query.filter_by(email=session['user_email']).first()  # Ambil user berdasarkan email yang sudah login

        if user and check_password_hash(user.password, current_password):
            if new_password == confirm_password:
                user.password = generate_password_hash(new_password)
                db.session.commit()
                flash('Password berhasil diubah!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Password baru dan konfirmasi tidak cocok!', 'danger')
        else:
            flash('Password saat ini salah!', 'danger')

    return render_template('reset_password.html')

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Ambil user yang sedang login
        user = User.query.get(current_user.id)

        if user and check_password_hash(user.password, current_password):
            if new_password == confirm_password:
                user.password = generate_password_hash(new_password)
                db.session.commit()
                flash('Password berhasil diubah!', 'success')
                return redirect(url_for('account'))
            else:
                flash('Password baru dan konfirmasi tidak cocok!', 'danger')
        else:
            flash('Password saat ini salah!', 'danger')

    return render_template('account.html')

@app.route('/dashboard')
@login_required
def dashboard():
    page = request.args.get('page', 1, type=int)  # Mendapatkan nomor halaman dari query string
    pets_per_page = 5  # Jumlah hewan per halaman
    pets = Pet.query.paginate(page=page, per_page=pets_per_page)  # Memanggil paginate dengan argumen yang benar

    # Menghitung total hewan peliharaan berdasarkan spesies
    total_pets = Pet.query.count()
    total_dogs = Pet.query.filter_by(species='Dog').count()
    total_cats = Pet.query.filter_by(species='Cat').count()

    return render_template('dashboard.html', 
                           pets=pets.items, 
                           total_pets=total_pets, 
                           total_dogs=total_dogs, 
                           total_cats=total_cats, 
                           current_page=pets.page, 
                           total_pages=pets.pages)

@app.route('/add_pet', methods=['GET', 'POST'])
@login_required
def add_pet():
    form = PetForm()
    if form.validate_on_submit():
        new_pet = Pet(name=form.name.data, species=form.species.data, breed=form.breed.data,
                    age=form.age.data, weight=form.weight.data, owner_id=current_user.id)
        db.session.add(new_pet)
        db.session.commit()
        flash('Pet added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_pet.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/edit_pet/<int:pet_id>', methods=['GET', 'POST'])
@login_required
def edit_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    form = PetForm(obj=pet)
    if form.validate_on_submit():
        pet.name = form.name.data
        pet.species = form.species.data
        pet.breed = form.breed.data
        pet.age = form.age.data
        pet.weight = form.weight.data
        db.session.commit()
        flash('Pet updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_pet.html', form=form, title='Edit Pet')

@app.route('/delete_pet/<int:pet_id>', methods=['POST'])
@login_required
def delete_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    db.session.delete(pet)
    db.session.commit()
    flash('Pet deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)