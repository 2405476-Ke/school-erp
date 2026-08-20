# Build stage
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
# Explicitly install vite globally just in case the generated package.json is missing it
RUN npm install -g vite
COPY . .
# Using environment variable placeholder so it can be replaced by nginx or built properly
ENV VITE_API_BASE_URL=/api
RUN npm run build

# Production stage
FROM nginx:alpine
# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html
# Add custom nginx config for React/SPA routing and API proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
