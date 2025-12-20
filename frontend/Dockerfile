# 1. Сборка (Node.js)
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Собираем проект в папку dist
RUN npm run build

# 2. Раздача (Nginx)
FROM nginx:alpine
# Копируем собранные файлы из предыдущего этапа
COPY --from=build /app/dist /usr/share/nginx/html
# Настройка Nginx для SPA (чтобы работали роуты /interview, /resume)
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]