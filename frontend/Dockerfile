FROM node:26-alpine@sha256:e88a35be04478413b7c71c455cd9865de9b9360e1f43456be5951032d7ac1a66 AS build
WORKDIR /app
RUN corepack enable
COPY package.json yarn.lock .yarnrc.yml ./
RUN --mount=type=cache,target=/root/.yarn/berry/cache,sharing=locked \
    yarn install --immutable
COPY . .
RUN yarn build

FROM nginx:alpine@sha256:4a73073bd557c65b759505da037898b61f1be6cbcc3c2c3aeac22d2a470c1752
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80