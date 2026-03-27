# Hussam Quantum Container
FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install numpy

CMD ["python", "Hussam_Al_Kami.py"]
