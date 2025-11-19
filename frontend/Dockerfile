FROM node:25-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
# Expose Vite dev server port
EXPOSE 3000
# Start dev server (--host 0.0.0.0 allows external connections)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]   