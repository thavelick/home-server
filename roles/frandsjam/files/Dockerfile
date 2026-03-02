FROM node:20

WORKDIR /app

COPY package.json .
RUN npm install

COPY server.js .

EXPOSE 2567

CMD ["node", "server.js"]
