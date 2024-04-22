import os
import psycopg2
from psycopg2 import pool
from urllib.parse import urlparse


class DatabaseManager:
    def __init__(self):
        self.pool = self.create_connection_pool()

    @staticmethod
    def create_connection_pool():
        database_url = os.getenv('DB_URL')  # Expecting a full URL in the environment variable
        if not database_url:
            print("Database URL is not set in environment variables.")
            return None

        # Parse the database URL
        parsed_url = urlparse(database_url)

        # Extract components from the URL
        db_name = parsed_url.path[1:]  # Remove the leading slash
        user = parsed_url.username
        password = parsed_url.password
        host = parsed_url.hostname
        port = parsed_url.port if parsed_url.port else 5432  # Default port for PostgreSQL if not specified

        try:
            return psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                user=user,
                password=password,
                host=host,
                port=port,
                database=db_name
            )
        except psycopg2.OperationalError as e:
            print(f"Error creating connection pool: {e}")
            return None

    def get_connection(self):
        if self.pool:
            return self.pool.getconn()
        else:
            return None

    def free_connection(self, conn):
        if self.pool:
            self.pool.putconn(conn)

    def fetch_course_names(self):
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT DISTINCT course_name FROM presentations")
                    courses = cursor.fetchall()
                    return [course[0] for course in courses]
            except Exception as e:
                print(f"Failed to fetch course names: {e}")
            finally:
                self.free_connection(conn)
        return []

    def fetch_presentation_numbers(self, course_name):
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT p_id FROM presentations WHERE course_name = %s ORDER BY p_id",
                        (course_name,)
                    )
                    presentations = cursor.fetchall()
                    return [str(presentation[0]) for presentation in presentations]
            except Exception as e:
                print(f"Failed to fetch presentation numbers for {course_name}: {e}")
            finally:
                self.free_connection(conn)
        # Return an empty list if no presentations are found
        return []

    def get_presentation_path(self, course_name, presentation_number):
        """
        Retrieves the file path of a presentation from the database.
        """
        conn = self.get_connection()
        if conn is not None:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT file_path"
                        "      FROM presentations"
                        "      WHERE course_name = %s AND p_id = %s",
                        (course_name, presentation_number)
                    )
                    # For debugging purposes
                    print(f"Fetching presentation {presentation_number} for course {course_name}")
                    result = cursor.fetchone()
                    # Return the file path if found
                    return result[0] if result else None
            except Exception as e:
                print(f"Failed to retrieve data: {e}")
            # Close the connection
            finally:
                self.free_connection(conn)
        # Return None if no file path is found
        # url = f"postgresql://postgres:Admin244199@localhost:5432/telegramBot"
        return None
