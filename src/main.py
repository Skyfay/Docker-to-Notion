import os
import docker
import requests
import json
from datetime import datetime
import time
import logging
from packaging import version
import socket

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Notion API settings
NOTION_API_KEY = os.environ.get('NOTION_API_KEY')
NOTION_DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')
NOTION_API_URL = "https://api.notion.com/v1"

# Registry credentials
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY', '')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY', '')
AWS_REGION = os.environ.get('AWS_REGION', 'eu-central-1')

# Excluded images setting
try:
    EXCLUDED_IMAGES = json.loads(os.environ.get('EXCLUDED_IMAGES', '[]'))
    if not isinstance(EXCLUDED_IMAGES, list):
        logger.warning("EXCLUDED_IMAGES must be a JSON array. Using empty list instead.")
        EXCLUDED_IMAGES = []
except json.JSONDecodeError:
    logger.warning("Failed to parse EXCLUDED_IMAGES. Using empty list instead.")
    EXCLUDED_IMAGES = []

# Initialize Docker client
docker_client = docker.from_env()

def get_server_name():
    """Get the server name"""
    # First try to read hostname from mounted file
    hostname_file = "/etc/hostname"
    if os.path.exists(hostname_file):
        try:
            with open(hostname_file, 'r') as f:
                hostname = f.read().strip()
                if hostname:
                    return hostname
        except Exception as e:
            logger.warning(f"Error reading {hostname_file}: {str(e)}")
    
    # Fallback: Try to get hostname via socket
    try:
        return socket.gethostname()
    except:
        return "unknown-server"

def get_docker_images():
    """Get all Docker images from the system"""
    images = docker_client.images.list()
    image_list = []
    excluded_count = 0
    
    for image in images:
        tags = image.tags
        if not tags:  # Skip images without tags
            continue
            
        for tag in tags:
            try:
                if ':' in tag:
                    repo_with_registry, tag_version = tag.split(':')
                else:
                    repo_with_registry, tag_version = tag, 'latest'
                
                # Check if this image should be excluded
                skip_image = False
                for excluded_pattern in EXCLUDED_IMAGES:
                    if excluded_pattern in repo_with_registry:
                        logger.info(f"Excluding image: {tag} (matches exclusion pattern: {excluded_pattern})")
                        excluded_count += 1
                        skip_image = True
                        break
                
                if skip_image:
                    continue
                
                # Separate registry and repository
                parts = repo_with_registry.split('/')
                if '.' in parts[0] or parts[0] == 'ghcr.io' or 'ecr.aws' in parts[0]:
                    # Custom registry
                    registry = parts[0]
                    repo = '/'.join(parts[1:])
                else:
                    # Docker Hub
                    registry = 'docker.io'
                    repo = repo_with_registry
                
                # Ensure we have a valid timestamp
                try:
                    # Check if 'Created' is an int/float
                    created_timestamp = image.attrs.get('Created')
                    if isinstance(created_timestamp, (int, float)):
                        created_time = datetime.fromtimestamp(created_timestamp)
                    else:
                        # If it's a string, try to parse ISO format
                        created_time = datetime.fromisoformat(created_timestamp.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    created_time = datetime.now()  # Fallback if parsing fails
                
                # Calculate size correctly
                try:
                    size = float(image.attrs.get('Size', 0)) / (1024 * 1024)
                except (ValueError, TypeError):
                    size = 0.0
                
                image_list.append({
                    'registry': registry,
                    'repo': repo,
                    'tag': tag_version,
                    'id': image.id.split(':')[1][:12] if ':' in image.id else image.id[:12],
                    'created': created_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'size': f"{size:.2f} MB"
                })
            except Exception as e:
                logger.error(f"Error processing image {tag}: {str(e)}")
                continue
    
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} image(s) from the list")
    
    return image_list

def check_for_updates(image_list):
    """Check if updates are available for the images"""
    for image in image_list:
        registry = image['registry']
        repo = image['repo']
        current_tag = image['tag']
        
        try:
            if registry == 'docker.io':
                # Docker Hub API (works without authentication for public images)
                if '/' not in repo:
                    repo = f"library/{repo}"
                
                url = f"https://registry.hub.docker.com/v2/repositories/{repo}/tags"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    latest_version = find_latest_version(data.get('results', []), current_tag)
                    image['update_available'] = latest_version if latest_version else "No"
                else:
                    image['update_available'] = "Unknown"
            
            elif registry == 'ghcr.io':
                # GitHub Container Registry
                if not GITHUB_TOKEN:
                    image['update_available'] = "GitHub Token required"
                    continue
                
                headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
                
                # Extract owner/repo from the repository path
                owner_repo = repo
                
                # Use GitHub API for container packages
                url = f"https://api.github.com/orgs/{owner_repo.split('/')[0]}/packages/container/{owner_repo.split('/')[1]}/versions"
                
                # Try with Organizations API
                response = requests.get(url, headers=headers)
                
                # If that doesn't work, try with User API
                if response.status_code != 200:
                    url = f"https://api.github.com/users/{owner_repo.split('/')[0]}/packages/container/{owner_repo.split('/')[1]}/versions"
                    response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    tags = []
                    for version_data in data:
                        for tag in version_data.get('metadata', {}).get('container', {}).get('tags', []):
                            tags.append({"name": tag})
                    
                    latest_version = find_latest_version(tags, current_tag)
                    image['update_available'] = latest_version if latest_version else "No"
                elif response.status_code == 401:
                    image['update_available'] = "Invalid GitHub Token"
                else:
                    logger.warning(f"GitHub API Error: {response.status_code}, {response.text}")
                    image['update_available'] = f"GitHub API Error: {response.status_code}"
            
            elif 'ecr.aws' in registry:
                # Amazon ECR
                if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
                    image['update_available'] = "AWS credentials required"
                    continue
                
                import boto3
                
                try:
                    # Determine if it's a public or private ECR
                    is_public = 'public.ecr.aws' in registry
                    
                    # Extract region information from registry
                    region = AWS_REGION
                    if '.' in registry and len(registry.split('.')) >= 4:
                        region = registry.split('.')[3]
                    
                    # Determine repository name
                    repository_name = repo.split('/')[-1]
                    
                    # Create ECR client
                    if is_public:
                        client = boto3.client(
                            'ecr-public',
                            region_name=region,
                            aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_KEY
                        )
                        
                        response = client.describe_image_tags(
                            repositoryName=repository_name
                        )
                        
                        tags = []
                        for tag_detail in response.get('imageTagDetails', []):
                            tags.append({"name": tag_detail.get('imageTag')})
                        
                    else:
                        client = boto3.client(
                            'ecr',
                            region_name=region,
                            aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_KEY
                        )
                        
                        response = client.describe_images(
                            repositoryName=repository_name
                        )
                        
                        tags = []
                        for image_detail in response.get('imageDetails', []):
                            for tag in image_detail.get('imageTags', []):
                                tags.append({"name": tag})
                    
                    latest_version = find_latest_version(tags, current_tag)
                    image['update_available'] = latest_version if latest_version else "No"
                except Exception as e:
                    logger.error(f"AWS ECR API Error: {str(e)}")
                    image['update_available'] = f"AWS ECR Error: {str(e)}"
            
            else:
                # Generic registry - not supported
                image['update_available'] = "Registry not supported"
        
        except Exception as e:
            logger.error(f"Error checking updates for {registry}/{repo}:{current_tag}: {str(e)}")
            image['update_available'] = "Error"
    
    return image_list

def find_latest_version(tags, current_tag):
    """Find the latest version from a list of tags"""
    if current_tag in ['latest', 'main', 'master']:
        return None
    
    latest_version = None
    
    # Try to detect semantic versioning
    try:
        # Clean current tag for version checking
        clean_current = current_tag
        if current_tag.startswith('v') and current_tag[1:].replace('.', '').isdigit():
            clean_current = current_tag[1:]
            
        # Check all tags
        for tag_data in tags:
            tag_name = tag_data.get('name')
            
            # Skip special tags
            if not tag_name or tag_name in ['latest', 'main', 'master']:
                continue
            
            # Clean tag name for version checking
            clean_tag = tag_name
            if tag_name.startswith('v') and tag_name[1:].replace('.', '').isdigit():
                clean_tag = tag_name[1:]
            
            # Try to compare versions
            try:
                if version.parse(clean_tag) > version.parse(clean_current):
                    if latest_version is None or version.parse(clean_tag) > version.parse(latest_version.replace('v', '') if latest_version.startswith('v') else latest_version):
                        latest_version = tag_name
            except Exception:
                # Ignore non-semantic tags
                pass
    except Exception as e:
        logger.debug(f"Error comparing versions: {str(e)}")
    
    return latest_version

def update_notion_database(image_list):
    """Update the Notion database with image information"""
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Get current server name
    server_name = get_server_name()
    logger.info(f"Detected server name: {server_name}")
    
    # First get all existing entries
    existing_entries = {}
    query_url = f"{NOTION_API_URL}/databases/{NOTION_DATABASE_ID}/query"
    response = requests.post(query_url, headers=headers)
    
    if response.status_code == 200:
        results = response.json().get('results', [])
        for result in results:
            props = result.get('properties', {})
            try:
                image_id = props.get('Image ID', {}).get('rich_text', [])[0].get('plain_text', '')
                # Store the server name too to find the right entries
                server = ""
                try:
                    server_texts = props.get('Server', {}).get('rich_text', [])
                    if server_texts:
                        server = server_texts[0].get('plain_text', '')
                except:
                    pass
                
                # Unique key: Image ID + Server
                existing_entries[f"{image_id}_{server}"] = result.get('id')
                # Store entry without server as fallback
                existing_entries[image_id] = result.get('id')
            except (IndexError, KeyError):
                continue
    
    # For each Docker image, create or update an entry
    for image in image_list:
        image_id = image['id']
        
        # Base data for all systems - removed Created on and Last checked
        page_data = {
            "properties": {
                "Repository": {"title": [{"text": {"content": image['repo']}}]},
                "Registry": {"rich_text": [{"text": {"content": image['registry']}}]},
                "Tag": {"rich_text": [{"text": {"content": image['tag']}}]},
                "Image ID": {"rich_text": [{"text": {"content": image_id}}]},
                "Size": {"rich_text": [{"text": {"content": image['size']}}]},
                "Update available": {"rich_text": [{"text": {"content": str(image['update_available'])}}]},
                "Server": {"rich_text": [{"text": {"content": server_name}}]}
            }
        }
        
        # Search for matching entry with server
        entry_key = f"{image_id}_{server_name}"
        page_id = existing_entries.get(entry_key)
        
        # If no entry with this server was found, check without server
        if not page_id:
            # Try with just the Image ID (for backward compatibility)
            page_id = existing_entries.get(image_id)
            
            # If an entry without server was found and the server is empty, update it
            if page_id:
                # Check if the entry already has a server
                query_url = f"{NOTION_API_URL}/pages/{page_id}"
                response = requests.get(query_url, headers=headers)
                
                if response.status_code == 200:
                    props = response.json().get('properties', {})
                    try:
                        server_texts = props.get('Server', {}).get('rich_text', [])
                        existing_server = server_texts[0].get('plain_text', '') if server_texts else ""
                        
                        # If the entry already has a different server, create a new entry
                        if existing_server and existing_server != server_name:
                            page_id = None
                    except:
                        pass
        
        if page_id:
            # Update existing entry
            update_url = f"{NOTION_API_URL}/pages/{page_id}"
            response = requests.patch(update_url, headers=headers, data=json.dumps(page_data))
            if response.status_code == 200:
                logger.info(f"Updated entry for {image['registry']}/{image['repo']}:{image['tag']} on server {server_name}.")
            else:
                logger.error(f"Error updating entry: {response.text}")
        else:
            # Create new entry
            page_data["parent"] = {"database_id": NOTION_DATABASE_ID}
            create_url = f"{NOTION_API_URL}/pages"
            response = requests.post(create_url, headers=headers, data=json.dumps(page_data))
            if response.status_code == 200:
                logger.info(f"Created new entry for {image['registry']}/{image['repo']}:{image['tag']} on server {server_name}.")
            else:
                logger.error(f"Error creating entry: {response.text}")

def main():
    """Main function"""
    # Check if Notion credentials are set
    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        logger.error("Notion API key or database ID is missing. Please set the environment variables.")
        return
    
    # Ensure CHECK_INTERVAL is an integer
    try:
        interval = int(os.environ.get('CHECK_INTERVAL', '3600'))
    except ValueError:
        logger.warning("CHECK_INTERVAL is not a valid integer. Using default value 3600.")
        interval = 3600
    
    # Log the excluded images
    if EXCLUDED_IMAGES:
        logger.info(f"Configured to exclude the following image patterns: {EXCLUDED_IMAGES}")
    
    while True:
        try:
            logger.info("Starting Docker image scan...")
            images = get_docker_images()
            logger.info(f"Found {len(images)} Docker images.")
            
            logger.info("Checking for updates...")
            updated_images = check_for_updates(images)
            
            logger.info("Updating Notion database...")
            update_notion_database(updated_images)
            
            logger.info(f"Scan completed. Next scan in {interval} seconds.")
            time.sleep(interval)
        
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            # More detailed error information for debugging
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            time.sleep(60)  # Wait 1 minute before trying again in case of errors

if __name__ == "__main__":
    main()