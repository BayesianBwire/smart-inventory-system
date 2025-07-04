from models.v1.user_model import User  # Make sure this import matches your project
from models import db

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        full_name = form.full_name.data
        password = form.password.data
        confirm_password = form.confirm_password.data

        # 🔒 Check password match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return render_template('register.html', form=form)

        # 🔍 Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with that email already exists.', 'danger')
            return render_template('register.html', form=form)

        # ✅ Create and save new user
        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
        )
        new_user.password = password  # This uses your @password.setter

        db.session.add(new_user)
        db.session.commit()

        flash('✅ Account created! Please check your email to confirm your address.', 'success')
        return redirect(url_for('login'))  # You can change this

    return render_template('register.html', form=form)
