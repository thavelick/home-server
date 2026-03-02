FROM node:20-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY package.json .
RUN npm install --omit=dev

COPY server.js .

EXPOSE 2567

CMD ["node", "server.js"]
