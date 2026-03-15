FROM eclipse-temurin:17-jdk
RUN useradd -m runner
USER runner
WORKDIR /code
