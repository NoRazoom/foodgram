FROM python:3.10
WORKDIR /app
# либо сервер перегружен, либо РКН балуется - 18.03.2026
RUN pip config set global.index-url https://pypi.mirrors.ustc.edu.cn/simple/ && \
    pip config set global.timeout 100 && \
    pip config set global.trusted-host pypi.mirrors.ustc.edu.cn
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]
