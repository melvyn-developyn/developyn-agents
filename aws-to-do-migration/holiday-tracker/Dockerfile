FROM node:12-slim

ENV NODE_ENV=development \
    PORT=3000

WORKDIR /app

COPY package.json ./
RUN npm install --production

COPY . .

EXPOSE 3000

CMD ["node", "bin/wwww"]