IMAGE_URL=${1:-apichatengine}
PORT=8080
docker run -p 8000:${PORT} -e PORT=${PORT} $IMAGE_URL
