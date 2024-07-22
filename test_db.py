from app import db, User

def test_db():
    # Print all users to see if the query works
    try:
        users = User.query.all()
        if users:
            for user in users:
                print(f"User: {user.username}, Password: {user.password}")
        else:
            print("No users found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    test_db()
