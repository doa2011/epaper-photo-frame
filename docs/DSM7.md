# DSM7 部署与验收（实验版）
在支持 Docker Compose 的 DSM7 Container Manager 上使用研发分支。尚未在真实群晖验证；旧版 Docker 套件的 Compose 兼容性需单独确认。
将 feature/image-pipeline 分支源码放到独立项目目录，照片目录与项目目录分离。创建 .env（不要提交）：
```dotenv
PHOTO_DIRECTORY=/volume1/photo
PHOTO_BIND_ADDRESS=127.0.0.1
PHOTO_PORT=8080
PHOTO_API_TOKEN=REPLACE_WITH_RANDOM_SECRET
```
使用随机长 token，确保 UID/GID 10001 对照片及父目录具有必要读取和遍历权限，不要递归放宽整个照片库权限。通过 SSH 在项目目录执行：
```sh
docker compose config --quiet
docker compose up -d --build
docker compose ps
```
在 NAS 本机验证（TOKEN 为实际值）：
```sh
curl -fsS -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8080/api/health
curl -fsS -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8080/api/photos
curl -fsS -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8080/api/devices
curl -fsS -G -H "Authorization: Bearer $TOKEN" --data-urlencode "photo=example.jpg" --data-urlencode "device=blozi-1280x800" http://127.0.0.1:8080/api/preview -o preview.png
```
将 example.jpg 替换为列表中实际相对路径。预期输出 PNG 1280×800；也可选择实际 /api/devices 返回的四色候选型号进行预览。预览不是硬件显示确认。
远程访问优先 SSH 端口转发或配置 HTTPS 反向代理；默认不向 LAN 暴露。不要将明文 HTTP 或 token 暴露至公网。已有基础浏览器 WebUI（实验版），可通过已配置的访问地址打开；仍需真实浏览器与 DSM7 实机验收。
异常检查：docker compose logs --tail=100；检查目录存在、权限、端口冲突、token 配置。日志分享前删除敏感信息。停止：docker compose down；不会删除绑定的照片目录。
验收：健康检查通过、未认证请求 401、照片列表非空、预览尺寸正确、照片挂载只读。Docker CI 已覆盖基础容器运行及合成样本转换，DSM7 实机验收仍待执行。
