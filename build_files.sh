python manage.py collectstatic --noinput
mkdir -p staticfiles/media
cp -R media/. staticfiles/media/
