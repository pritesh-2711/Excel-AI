.PHONY: build up down logs restart clean start app-logs shell status

COMPOSE_FILE := docker-compose.bridge.yml

# Build Docker image
build:
	docker-compose -f $(COMPOSE_FILE) build

# Start containers
up:
	docker-compose -f $(COMPOSE_FILE) up -d

# Stop containers
down:
	docker-compose -f $(COMPOSE_FILE) down

# View logs
logs:
	docker-compose -f $(COMPOSE_FILE) logs -f

# Restart containers
restart:
	docker-compose -f $(COMPOSE_FILE) restart

# Stop and remove containers, volumes, images
clean:
	docker-compose -f $(COMPOSE_FILE) down -v --rmi all

# Build and start
start: build up

# View app logs only
app-logs:
	docker-compose -f $(COMPOSE_FILE) logs -f ai-excel

# Enter container shell
shell:
	docker-compose -f $(COMPOSE_FILE) exec ai-excel /bin/bash

# Check container status
status:
	docker-compose -f $(COMPOSE_FILE) ps