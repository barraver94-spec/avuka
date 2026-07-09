# gunicorn config — נטען אוטומטית ע"י gunicorn מתיקיית העבודה.
# worker אחד כדי לא לחרוג מזיכרון 512MB (Render Starter). מיחזור תקופתי מונע דליפות.
# הערה: ארגומנט CLI מפורש (--workers N) גובר על הקובץ הזה.
workers = 1
timeout = 120
max_requests = 50
max_requests_jitter = 10
