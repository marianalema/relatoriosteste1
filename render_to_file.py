from app import app, generate_captcha, db
import os

@app.route('/render_login')
def render_login():
    captcha_question, captcha_answer = generate_captcha()
    rendered_html = render_template('login.html', captcha_question=captcha_question)
    
    if not os.path.exists('docs'):
        os.makedirs('docs')
    
    with open('docs/login.html', 'w') as file:
        file.write(rendered_html)
    return 'Login page rendered to docs/login.html'

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
