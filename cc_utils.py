import re
import discord
import base64
import asyncio
import requests
from urllib.parse import urlparse, unquote
from config import VIRUSTOTAL_API_KEY

async def on_mal_msg(message):
    audit_reason = f'Posted a link that was flagged as malicious by the CRYPTCADA bot, the message has been deleted.'
    warn_reason = f'You posted a link that was flagged as malicious by the CRYPTCADA bot and it has been deleted, please refrain from posting malicious links in the server. \n \n *If you think this was a mistake, please open a ticket.*'
    await message.delete()

    # After deleting the message, send a message to the channel to let people know of the event.
    deleted_embed = discord.Embed(
        description=f'{message.author.mention} posted a link that was flagged as malicious, the message has been deleted. This event has been logged.',
        color=discord.Color.red())
    await message.channel.send(embed=deleted_embed)

    # Send a moderation log message to a moderation channel
    moderation_channel = discord.utils.get(message.guild.text_channels, name='cryptcada-logs')
    if moderation_channel:
        moderation_embed = discord.Embed(
            description=f'{message.author.mention} has been warned. \n \n **Reason:** \n {audit_reason} \n \n **Original message:** \n {message.author.mention}: "{stored_message}" ',
            color=discord.Color.red())
        await moderation_channel.send(embed=moderation_embed)
    else:
        nomod_embed = discord.Embed(
            description=f'Moderation log channel not found. Please set up the CRYPTCADA channels by running the %setup command.',
            color=discord.Color.red())
        await message.channel.send(embed=nomod_embed)

    # Send a warning message to the user
    await message.author.send(f'You have been warned in **"{message.guild.name}"** \n \n **Reason:** {warn_reason}')

async def on_safe_msg(message):
    safe_embed = discord.Embed(
        description=f'The above posted link was ***not*** flagged as malicious and is safe to click.',
        color=discord.Color.red())
    await message.channel.send(embed=safe_embed)

async def sanitize_urls(msg):

    # regex for urls
    url_re = r'(?:https?://|www\.)\S+'

    # list for all urls in msg
    urls = re.findall(url_re, msg)

    # if urls is empty, we can return the original msg, otherwise we continue and
    # check if the urls are malicious
    if not urls:
        return "OK"

    for url in urls:

        # unquote the url to get rid of any obfuscation that may or may not be present
        url = unquote(url)

        # encode url in base64 and send to VirusTotal API for threat detection
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        vt_url = ('https://www.virustotal.com/api/v3/urls/' + url_id)

        headers = {
            "accept": "application/json",
            'x-apikey': VIRUSTOTAL_API_KEY,
        }

        response = requests.get(vt_url, headers=headers)
        result = response.json()

        # check if the result flagged the url, and if it did, return error msg
        if 'data' in result:
            if result['data']['attributes']['last_analysis_stats']['malicious'] > 0:
                guild = msg.guild
                if guild:
                    return 'ERR'
                else: continue

        # if we get to this point, we know that all the urls passed the VirusTotal scan,
        # and we can deem the msg safe

        return "OK"




