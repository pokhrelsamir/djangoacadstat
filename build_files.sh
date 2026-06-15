if [ "$SKIP_MIGRATIONS" != "1" ]; then
  python manage.py migrate --noinput
fi
python manage.py collectstatic --noinput
mkdir -p staticfiles/media
cp -R media/. staticfiles/media/
