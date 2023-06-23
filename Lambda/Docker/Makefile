all:
	cd app && docker build -t docker-app .
	cd face_rec && docker build -t docker-face_rec .
	cd mail && docker build -t docker-mail .
	docker-compose up
