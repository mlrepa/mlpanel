sudo chown user $WORKSPACE

while ! pg_isready -h $DB_HOST -p $DB_PORT; do
  echo "Wait for db server..." && sleep 1s;
done;

uvicorn --host 0.0.0.0 --port 8080 src.app:app --reload