# Stage 1: Build
FROM node:18 AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Build arguments for environment variables
ARG VITE_SERVER_BASE_URL

ENV VITE_SERVER_BASE_URL=$VITE_SERVER_BASE_URL

RUN npm run build

# Stage 2: Nginx
FROM nginx:alpine
 
# Copy build output to Nginx html directory
COPY --from=build /app/dist /usr/share/nginx/html
 
EXPOSE 4173
CMD ["nginx", "-g", "daemon off;"]
  