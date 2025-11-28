FROM nginx:1.25-alpine

# 复制nginx主配置文件
COPY nginx.conf /etc/nginx/nginx.conf

# 复制站点配置
COPY conf.d/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]

