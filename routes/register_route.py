from flask import Flask, render_template, redirect, url_for, flash
from registration_form import RegisterForm  # Adjust the import path if needed
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Should be set from .env in production

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        # ✅ Secure the password
        hashed_password = generate_password_hash(password)

        # ⏳ TODO: Save to your user model/database here

        flash('Account created successfully!', 'success')
        return redirect(url_for('register'))  # You can change to dashboard/login after saving
    return render_template('register.html', form=form)
