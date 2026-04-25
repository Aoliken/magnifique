"""
Hotel Magnifique — Entry Point
"""
from app import create_app

app = create_app()


@app.route('/')
def home():
    """Página principal del juego."""
    from flask import render_template
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)