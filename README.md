<h1 align="center">Docker to Notion<br />
<div align="center">
<a href="https://github.com/skyfay/docker-to-notion"><img src="https://github.com/Skyfay/Docker-to-Notion/blob/main/.github/preview.png" title="Screenshot" style="max-width:100%;" width="832" /></a>
</div>
<div align="center">

![GitHub tag (latest SemVer pre-release)](https://img.shields.io/github/v/tag/Skyfay/Docker-to-Notion?label=Version)
![GitHub (Pre-)Release Date](https://img.shields.io/github/release-date-pre/Skyfay/Docker-To-Notion)
![GitHub contributors](https://img.shields.io/github/contributors/Skyfay/Docker-to-Notion)
![GitHub commit activity (branch)](https://img.shields.io/github/commit-activity/t/Skyfay/Docker-to-Notion)
![GitHub last commit (by committer)](https://img.shields.io/github/last-commit/Skyfay/Docker-to-Notion)
![Docker Pulls](https://img.shields.io/docker/pulls/skyfay/docker-to-notion)
![Discord](https://img.shields.io/discord/580801656707350529?label=Discord&color=%235865f2&link=https%3A%2F%2Fdiscord.com%2Finvite%2FYvgPyky)
![GitHub](https://img.shields.io/github/license/Skyfay/Docker-to-Notion)

</div></h1>

Docker images updates visualized in Notion.

## Features ✨

 - Get Images from the Docker Socket and send Updates to Notion
 - Exclude Images
 - Set a specific sync interval

## Usage  🐳

Via Docker Compose:

```yaml
version: '3.8'

services:
  app:
    image: skyfay/docker-to-notion:latest
    container_name: docker-to-notion
    hostname: your-hostname # Not needed if you use linux and /etc/hostname
    environment:
      - NOTION_AUTH_TOKEN=your_notion_token
      - NOTION_DATABASE_ID=your_database_id
      - EXCLUDED_IMAGES=["skyfay/docker-to-notion"] # [] = exclude no images, ["image", "image2"] = exclude multiple images
      - SYNC_INTERVAL=300  # the lowest value is 300 / 5 minutes
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /etc/hostname:/etc/hostname:ro # Linux only instead use docker hostname above
    restart: unless-stopped
```
Via Docker CLI:
```
docker run -it --rm \
  --name docker-to-notion \
  --hostname your-hostname \
  -e NOTION_AUTH_TOKEN=your_notion_token \
  -e NOTION_DATABASE_ID=your_database_id \
  -e EXCLUDED_IMAGES='["skyfay/docker-to-notion"]' \
  -e SYNC_INTERVAL=300 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /etc/hostname:/etc/hostname:ro \
  skyfay/docker-to-notion:latest
```

## FAQ 💬

### Create your Database in Notion

Create a Notion Database and add the following columns:

<img width="289" alt="image" src="https://github.com/user-attachments/assets/975d0803-659c-4836-a950-7e3ce421eb6d">

It doesn't matter in which order, but the names and types must match exactly.

| Type  | Name |
| ------------- | ------------- |
| Title  | Container Name  |
| Text  | Server Name  |
| Text  | Image  |
| Text  | Current Tag  |
| Text  | Current Version  |
| Text  | New Version  |
| Text  | Local Digest  |
| Text  | Remote Digest  |
| Checkbox | Needs Update  |
| Checkbox | Newer Tag Available |


### How to get your Notion token?
First of all go to your Notion intigrations: https://www.notion.so/profile/integrations

1. Create a new intigration
<img width="1205" alt="image" src="https://github.com/user-attachments/assets/ac192407-b50c-4da9-9935-e6b9dc7c1fc1">

2. Add a intigration name, select your workspace and save
<img width="1375" alt="image" src="https://github.com/user-attachments/assets/b12bedde-50a6-46c5-9ea4-0605926977b3">

3. Go to the intigration and copy your Notion Token = Internal Integration Secret
<img width="1340" alt="image" src="https://github.com/user-attachments/assets/7944b534-f41f-4316-96b9-ce90b968de0c">

### How to get the Notion database ID

Visit Notion via Web Browser: https://www.notion.so/login

1. Go to your Database and open it full screen and copy the database ID from your WEB URL
<img width="1672" alt="image" src="https://github.com/user-attachments/assets/82c5f228-2290-4b46-8fe9-57e0f59edd67">

2. Add the intigration you created to the notion database to give access
<img width="1592" alt="image" src="https://github.com/user-attachments/assets/04f26280-c90e-43fc-8f54-ef0ceb712978">
