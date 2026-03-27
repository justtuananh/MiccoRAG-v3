# Stage 1: Build
FROM node:18-alpine AS build

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build the app
# Use the production env if created, otherwise default VITE_API_URL can be injected at build time
RUN pnpm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built assets to Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port (internal to docker network)
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
