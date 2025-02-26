FROM python:3.12-slim

WORKDIR /app

COPY ../requirements.txt ./requirements.txt  

RUN pip3 install -r requirements.txt

EXPOSE 8501

COPY . .
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
