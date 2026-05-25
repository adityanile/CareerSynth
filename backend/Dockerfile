FROM nilecr.azurecr.io/careersynth-backend-env:latest

WORKDIR /app

COPY . /app

EXPOSE 8888

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8888"]
