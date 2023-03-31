import sqlite3


def create_bd():
    """Function to create sqlite database to keep results of all users"""
    try:
        open("data.sqlite")
    except FileNotFoundError:
        con = sqlite3.connect("data.sqlite")
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE locality (
                user_id INTEGER PRIMARY KEY,
                latitude FLOAT NOT NULL,
                longitude FLOAT NOT NULL
            )
        """)
        con.commit()


def insert_lat_lon_in_database(user_id: int, latitude: float, longitude: float):
    """Function to add a new recording to database"""
    create_bd()
    con = sqlite3.connect("data.sqlite")
    cur = con.cursor()
    try:
        cur.execute(f"""
                    INSERT INTO locality (user_id, latitude, longitude)
                    VALUES ({user_id}, {latitude}, {longitude})
                """)
    except sqlite3.IntegrityError:
        cur.execute(f"""
                        UPDATE locality SET
                        latitude = {latitude}, longitude = {longitude}
                        WHERE user_id = {user_id}
                        """)
    con.commit()
    

def get_lat_lon_by_user_id(user_id: int) -> (float, float):
    con = sqlite3.connect("data.sqlite")
    cur = con.cursor()
    res = cur.execute(f"""
                        SELECT latitude, longitude
                        FROM locality
                        WHERE user_id = {user_id}
                    """).fetchone()
    return res