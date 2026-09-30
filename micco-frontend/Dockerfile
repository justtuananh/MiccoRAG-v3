FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .

# Production must use same-origin /api routes and must never bundle dev auth bypass.
ENV VITE_SKIP_AUTH=false \
    VITE_API_BASE_URL= \
    VITE_RAGV2_BASE_URL= \
    VITE_FORCE_SAME_ORIGIN_API=true
RUN npm run build

FROM nginx:stable-alpine

ARG VCS_REF=unknown
LABEL org.opencontainers.image.revision="$VCS_REF"

COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build --chown=nginx:nginx /app/dist/ /usr/share/nginx/html/

# nginx runs without root: listen on 8080 and keep PID and temp files under /tmp.
RUN mkdir -p /tmp/nginx/client_body /tmp/nginx/proxy /tmp/nginx/fastcgi /tmp/nginx/uwsgi /tmp/nginx/scgi \
    && chown -R nginx:nginx /tmp/nginx /usr/share/nginx/html
USER nginx

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/nginx-health || exit 1
CMD ["nginx", "-g", "daemon off;"]
