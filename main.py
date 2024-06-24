# CRYPTCADA by: GAZE | UzerZero In collaboration with Chiefu and xoxoxo

#    $$$$$$\  $$$$$$$\ $$\     $$\ $$$$$$$\ $$$$$$$$\  $$$$$$\   $$$$$$\  $$$$$$$\   $$$$$$\
#   $$  __$$\ $$  __$$\\$$\   $$  |$$  __$$\\__$$  __|$$  __$$\ $$  __$$\ $$  __$$\ $$  __$$\
#   $$ /  \__|$$ |  $$ |\$$\ $$  / $$ |  $$ |  $$ |   $$ /  \__|$$ /  $$ |$$ |  $$ |$$ /  $$ |
#   $$ |      $$$$$$$  | \$$$$  /  $$$$$$$  |  $$ |   $$ |      $$$$$$$$ |$$ |  $$ |$$$$$$$$ |
#   $$ |      $$  __$$<   \$$  /   $$  ____/   $$ |   $$ |      $$  __$$ |$$ |  $$ |$$  __$$ |
#   $$ |  $$\ $$ |  $$ |   $$ |    $$ |        $$ |   $$ |  $$\ $$ |  $$ |$$ |  $$ |$$ |  $$ |
#   \$$$$$$  |$$ |  $$ |   $$ |    $$ |        $$ |   \$$$$$$  |$$ |  $$ |$$$$$$$  |$$ |  $$ |
#    \______/ \__|  \__|   \__|    \__|        \__|    \______/ \__|  \__|\_______/ \__|  \__|


#imports
import os
import asyncio
import discord
from discord.ext import commands
import discord.ui
from discord.ui import Button, View
from discord import app_commands, Interaction, Embed, Color
import pycord
from urllib.parse import urlparse, unquote
import praw
import string
import secrets
import random
import binascii
import logging
import datetime
import threading
import time
from wordfilter import wordfilter
from cc_utils import on_mal_msg, sanitize_urls
from config import DISCORD_BOT_TOKEN, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, VIRUSTOTAL_API_KEY

# Configure the logger
logging.basicConfig(filename='bot_debug.log', level=logging.DEBUG)

# Log messages
logging.debug("Debugging message: This code is executed.")
logging.info("Information message: Something happened.")
logging.warning("Warning message: A potential issue occurred.")
logging.error("Error message: An error occurred.")

#intents
intents = discord.Intents.all()

# Initialize Discord bot
bot = commands.Bot(command_prefix='%', intents=intents)

# Initialize PRAW (Reddit API) client
reddit = praw.Reddit(client_id = REDDIT_CLIENT_ID,
                     client_secret = REDDIT_CLIENT_SECRET,
                     user_agent = REDDIT_USER_AGENT)

# Initialize Embed Messages
async def send_embed_message(ctx, content, color):
    embed = discord.Embed(description=content, color=color)
    return await ctx.send(embed=embed)

async def slash_embed_message(interaction, content: str, color: Color):
    embed = Embed(description=content, color=color)
    await interaction.response.send_message(embed=embed)

async def button_embed_message(interaction, content: str, color: Color, view):
    embed = Embed(description=content, color=color)
    view = view
    await interaction.response.send_message(embed=embed, view=view)

# Unregister the default 'help' command
bot.remove_command('help')

# List of meme subreddits
meme_subreddits = ['memes', 'dankmemes', 'wholesomememes', 'ProgrammerHumor']

# Initialize offensive_msg and set it to False
offensive_msg = False

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f"An error occurred: {e}")

@bot.event
async def on_message(message):
    vt_url = None # Initialize vt_url variable

    # check if the msg contains an url/s, and if it does, if it/they are malicious
    print("debugging line below")
    print(message.content)
    print(type(message.content))
    is_mal = await sanitize_urls(str(message.content).lower())

    # if the url/s is safe, we resume safely.
    # otherwise, we warn the sender, log the event, and delete the message
    if is_mal == "OK":
        print(f'returned safe')
    elif is_mal == "ERR":
        await on_mal_msg(message)

    # Delete messages that include bad words from a wordlist
    try:
        # Check if any of the words are in the wordlist
        if any(word in message.content.lower().split(' ') for word in wordfilter):
            offensive_msg = True
            stored_message = message.content # Store the message right away.
            await message.delete() # Delete the message in question.
            try:
                # Set audit and warn reasons
                audit_reason = f'Posted a message that was flagged as harmful or offensive by the CRYPTCADA bot, the message has been deleted.'
                warn_reason = f'You posted a message that was flagged as harmful or offensive by the CRYPTCADA bot and it has been deleted, please refrain from posting malicious links in the server. \n \n *If you think this was a mistake, please open a ticket.*'

                # After deleting the message, send a message to the channel to let people know of the event.
                deleted_embed = discord.Embed(description=f'{message.author.mention} posted a message that was flagged as harmful or offensive, the message has been deleted. This event has been logged.', color=discord.Color.red())
                await message.channel.send(embed=deleted_embed)

                # Send a moderation log message to a moderation channel
                moderation_channel = discord.utils.get(message.guild.text_channels, name='cryptcada-logs')
                if moderation_channel:
                    try:
                        moderation_embed = discord.Embed(description=f'{message.author.mention} has been warned. \n \n **Reason:** \n {audit_reason} \n \n **Original message:** \n {message.author.mention}: `{message.content}` ', color=discord.Color.red())
                        await moderation_channel.send(embed=moderation_embed)
                    except Exception as e:
                        print(f"An error occurred: {e}")
                # If there is no moderation channel, tell the server to use the %setup command.
                else:
                    nomod_embed = discord.Embed(description=f'Moderation log channel not found. Please set up the CRYPTCADA channels by running the /setup command.', color=discord.Color.red())
                    await message.channel.send(embed=nomod_embed)
            except Exception as e:
                print(f"An error occurred: {e}")
            # Send a warning message to the user
            try:
                await message.author.send(f'You have been warned in **"{message.guild.name}"** \n \n **Reason:** {warn_reason}')
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            offensive_msg = False
    except Exception as e:
        print(f"An error occurred: {e}")

    # Only let users call commands if the message doesn't contain a dangerous url or offensive words.
    if offensive_msg == False and is_mal != "ERR":
        await bot.process_commands(message)  # Process commands
    else:
        return

@bot.event
async def on_message_edit(before, after):

    vt_url = None # Initialize vt_url variable

    # check if the msg contains an url/s, and if it does, if it/they are malicious
    print("debugging line below")
    print(after.content)
    print(type(after.content))
    is_mal = await sanitize_urls(str(after.content).lower())

    # if the url/s is safe, we resume safely.
    # otherwise, we warn the sender, log the event, and delete the message
    if is_mal == "OK":
        print(f'returned safe')
    elif is_mal == "ERR":
        await on_mal_msg(after)

@bot.command(name='meme', description="Sends a random meme from reddit.")
async def meme(ctx):
    try:
        # Randomly select a subreddit from the list
        selected_subreddit = random.choice(meme_subreddits)

        # Scrape a meme from the selected subreddit
        subreddit = reddit.subreddit(selected_subreddit)
        post = subreddit.random()

        if post:
            # Convert the created_utc timestamp to a datetime object
            created_time = datetime.datetime.utcfromtimestamp(post.created_utc)

            # Add a link to the original post and mention the subreddit
            original_post_link = f"[View on Reddit in r/{post.subreddit.display_name}]({post.url})"

            # set the discord embed
            embed = discord.Embed(color=discord.Color.red())

            # Add the author's name and profile image
            embed.set_author(name=f'u/{post.author.name}', icon_url=post.author.icon_img)

            # Add the post's title
            embed.description = f'{post.title} \n {original_post_link}'

            # Add the image or video
            embed.set_image(url=post.url)

            # Display the time when it was posted
            embed.timestamp = created_time

            await ctx.send(embed=embed)
        else:
            await send_embed_message(ctx, f"No memes found in /r/{selected_subreddit}", discord.Color.red())
    except Exception as e:
        print(f"An error occurred: {e}")

# Function to provide text translation options with embed
async def provide_text_translation_options(ctx, text):
    # Create an embed with translation options
    embed = discord.Embed(title="Translation Options", color=discord.Color.red())
    embed.add_field(name="Text", value=text, inline=False)
    embed.add_field(name="Choose an option:", value=" 🇧 Binary \n 🇭 Hexadecimal \n 🧊 Chill++ ", inline=False)

    # Send the embed message
    message = await ctx.send(embed=embed)

    # Add reactions for translation options
    await message.add_reaction("🇧")  # Binary
    await message.add_reaction("🇭")  # Hexadecimal
    await message.add_reaction("🧊")  # Chill++

    # Wait for user reaction
    def reaction_check(reaction, user):
        return user == ctx.author and reaction.message == message and reaction.emoji in ["🇧", "🇭", "🧊"]

    try:
        reaction, user = await bot.wait_for("reaction_add", check=reaction_check, timeout=60)
    except asyncio.TimeoutError:
        await send_embed_message(ctx, f"You didn't choose an option in time.", discord.Color.red())
        return

    if reaction.emoji == "🇧":
        # Translate text to binary
        binary_text = ' '.join(format(ord(char), '08b') for char in text)
        await send_embed_message(ctx, f"Binary: ```{binary_text}```", discord.Color.red())
    elif reaction.emoji == "🇭":
        # Translate text to hexadecimal
        hex_text = ''.join(hex(ord(char))[2:] for char in text)
        await send_embed_message(ctx, f"Hexadecimal: ```{hex_text}```", discord.Color.red())
    elif reaction.emoji == "🧊":
        # Translate to "chill++" by converting to binary and then to "ice_cube" and "droplet"
        binary_text = ' '.join(format(ord(char), '08b') for char in text)
        chill_text = binary_text.replace('0', '🧊').replace('1', '💧')
        await send_embed_message(ctx, f"Chill++: ```{chill_text}```", discord.Color.red())

@bot.command(name='translate', description="Translate between different ciphers and encodings.")
async def translate(ctx, *, input_text):
    # Attempt to auto-detect the input type
    input_text = input_text.strip()
    if ' ' in input_text:
        # If there are spaces, assume it's binary or hexadecimal
        if all(c in '01 ' for c in input_text):
            # Binary contains only 0s, 1s, and spaces
            input_type = 'binary'
        elif all(c in '0123456789abcdefABCDEF ' for c in input_text):
            # Hexadecimal contains valid hex characters and spaces
            input_type = 'hexadecimal'
        elif all(c in '🧊💧 ' for c in input_text):
            # Chill++ contains valid chill++ characters
            input_type = 'chill++'
        else:
            input_type = 'text'
    else:
        # If no spaces, assume it's text
        input_type = 'text'

    if input_type == 'text':
        # Provide text translation options with embeds
        await provide_text_translation_options(ctx, input_text)
    elif input_type == 'binary':
        # Decode binary to text
        input_text = input_text.replace(' ', '')
        try:
            text = ''.join(chr(int(input_text[i:i+8], 2)) for i in range(0, len(input_text), 8))

            # check for malicious links inside decoded text
            if await sanitize_urls(text) == "ERR":
                await send_embed_message(ctx, "Message contained harmful content", discord.Color.red())
            else:
                await send_embed_message(ctx, f"Text: ```{text}```", discord.Color.red())

        except ValueError:
            await send_embed_message(ctx, "Invalid binary input.", discord.Color.red())


    elif input_type == 'hexadecimal':
        # Translate hexadecimal to text
        try:
            text = binascii.unhexlify(input_text.replace(" ", "")).decode('utf-8')

            # check for malicious links inside decoded text
            if await sanitize_urls(text) == "ERR":
                await send_embed_message(ctx, "Message contained harmful content", discord.Color.red())
            else:
                await send_embed_message(ctx, f"Text: ```{text}```", discord.Color.red())

        except (binascii.Error, UnicodeDecodeError):
            await send_embed_message(ctx, "Invalid hexadecimal input.", discord.Color.red())


    elif input_type == 'chill++':
        # Translate from "chill++" by converting from "ice_cube" and "droplet" to binary and then from binary to text"
        input_text = input_text.replace('🧊', "0").replace('💧', "1")
        input_text = input_text.replace(' ', '')
        try:
            text = ''.join(chr(int(input_text[i:i+8], 2)) for i in range(0, len(input_text), 8))

            # check for malicious links inside decoded text
            if await sanitize_urls(text) == "ERR":
                await send_embed_message(ctx, "Message contained harmful content", discord.Color.red())
            else:
                await send_embed_message(ctx, f"Text: ```{text}```", discord.Color.red())

        except ValueError:
            await send_embed_message(ctx, "Invalid chill++ input.", discord.Color.red())
    else:
        await send_embed_message(ctx, "Invalid input type. Use text, binary, hexadecimal or chill++.", discord.Color.red())

@bot.tree.command(name='ping', description="Sends the bot's latency.")
async def ping(ctx: Interaction):
    latency = round(bot.latency * 1000)  # Calculate the bot's latency in milliseconds
    await slash_embed_message(ctx, f'Pong! Latency: {latency}ms', discord.Color.red())

@bot.tree.command(name='search_reddit', description="Search reddit based on a query.")
async def search_reddit(ctx: Interaction, query: str):
    try:
        print(f'%search_reddit command ran with query: {query}')

        search_results = reddit.subreddit("all").search(query, sort="new", limit=50)
        displayed_posts = []
        new_posts = []

        new_posts.extend([post for post in search_results if post not in displayed_posts])
        random_posts = random.sample(new_posts, 3)
        has_ran = False

        async def send_posts(random_posts, first_call=False):
            embeds = []
            for post in random_posts:
                media_type = getattr(post.media, "type", None)
                print(f'post found: ""{post}"" with media type: {media_type}')
                created_time = datetime.datetime.utcfromtimestamp(post.created_utc)
                original_post_link = f"[View on Reddit in r/{post.subreddit.display_name}]({post.shortlink})"
                embed = discord.Embed(color=discord.Color.red())
                embed.set_author(name=f'u/{post.author.name}', icon_url=post.author.icon_img)
                embed.description = f'{original_post_link} \n **{post.title.strip("*")}** \n '

                if post.selftext:
                    embed.description += f'*{post.selftext.strip("*")}*'
                if media_type == "image":
                    embed.set_image(url=post.url)
                if media_type == "video":
                    embed.set_image(url=post.url)
                if f'youtube' in post.url or f'youtu.be' in post.url:
                    embed.description += f'\n<{post.url}>\n'
                    thumbnail_url = post.preview['images'][0]['source']['url']
                    embed.set_image(url=thumbnail_url)
                elif hasattr(post, 'preview') and 'images' in post.preview:
                    thumbnail_url = post.preview['images'][0]['source']['url']
                    embed.set_image(url=thumbnail_url)

                embed.timestamp = created_time

                if f'discord' not in post.url:
                    embeds.append(embed)
                    displayed_posts.append(post)
                    new_posts.remove(post)
                else:
                    print(f'discord link in post {post}')

            if first_call:
                await ctx.response.send_message(embeds=embeds)
            else:
                await ctx.followup.send(embeds=embeds)

            if len(new_posts) <= 1:
                await slash_embed_message(ctx, f'No more posts to display, please run the %search_reddit command again.', discord.Color.red())
                return

        async def prompt_more():
            buttonMore = Button(label="More posts", style=discord.ButtonStyle.green)
            buttonStop = Button(label="Stop searching", style=discord.ButtonStyle.red)

            embed = discord.Embed(color=discord.Color.red())
            embed.description = "Do you want to see more posts related to your query?"

            async def buttonMore_callback(button_interaction: Interaction):
                await button_interaction.response.edit_message(view=None)
                nonlocal has_ran
                has_ran = True
                new_posts.extend([post for post in search_results if post not in displayed_posts])
                random_posts = random.sample(new_posts, 3)
                await send_posts(random_posts)
                await prompt_more()

            async def buttonStop_callback(button_interaction: Interaction):
                await button_interaction.response.edit_message(view=None)

            buttonMore.callback = buttonMore_callback
            buttonStop.callback = buttonStop_callback

            view = View()
            view.add_item(buttonMore)
            view.add_item(buttonStop)

            await ctx.followup.send(embed=embed, view=view, ephemeral=True)

        if has_ran == False:
            await send_posts(random_posts, first_call=True)
            await prompt_more()

    except Exception as e:
        print(f"An error occurred: {e}")

@bot.tree.command(name='passwordgen', description="Generates a secure password and sends it privately through ephemeral responses.")
async def passwordgen(ctx: Interaction, length: int = 12):
    if length < 6:
        embed = discord.Embed(description="Password length should be at least 6 characters.", color=discord.Color.red())
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return
    elif length > 30:
        embed = discord.Embed(description="Password length can't be more than 30 characters.", color=discord.Color.red())
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return

    letters = string.ascii_letters
    digits = string.digits
    symbols = string.punctuation

    all_characters = letters + digits + symbols
    password = ''.join(secrets.choice(all_characters) for i in range(length))

    embed = discord.Embed(title="Your generated password:", description=f"`{password}`", color=discord.Color.red())
    await ctx.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='invite', description='Invite the bot to your own server!')
async def prompt_more_two(ctx: Interaction):
    buttonInv = Button(label="Invite CRYPTCADA", url="https://discord.com/oauth2/authorize?client_id=1158761436001091595&permissions=8&scope=bot+applications.commands", style=discord.ButtonStyle.link)
    view = View()
    view.add_item(buttonInv)
    await button_embed_message(ctx, "Click the button below to invite CRYPTCADA to your server!", discord.Color.red(), view)

@bot.tree.command(name='setup', description="Set up the CRYPTCADA category and log channel.")
async def setup(ctx: Interaction):
    # Check if setup has already been completed
    cryptcada_category = discord.utils.get(ctx.guild.categories, name='Cryptcada')
    cryptcada_logs_channel = discord.utils.get(ctx.guild.text_channels, name='cryptcada-logs')

    # Start auto_bump()
    await auto_bump(ctx)

    if not ctx.user.guild_permissions.administrator:
        await slash_embed_message(ctx, f'You do not have the necessary permissions to use this command.', discord.Color.red())
    else:
        if cryptcada_category and cryptcada_logs_channel:
            await slash_embed_message(ctx, 'Cryptcada channels and category have already been set up.', discord.Color.red())
        else:
            try:
                # Create Cryptcada category if not already existing
                if not cryptcada_category:
                    cryptcada_category = await ctx.guild.create_category('Cryptcada')

                # Create Cryptcada-logs channel if not already existing
                if not cryptcada_logs_channel:
                    cryptcada_logs_channel = await ctx.guild.create_text_channel('cryptcada-logs', category=cryptcada_category)

                # Set category permissions
                await cryptcada_category.set_permissions(ctx.guild.default_role, read_messages=False)
                await cryptcada_category.set_permissions(ctx.guild.me, read_messages=True)  # Allow the bot to read messages in the category

                await slash_embed_message(ctx, f'Cryptcada channels and category have been set up successfully.', discord.Color.red())
            except Exception as e:
                print(f"An error occurred: {e}")

@bot.tree.command(name='help', description="Tells you all the available commands.")
async def help(ctx: Interaction):
    # Define a dictionary of commands and their explanations with formatting
    commands_info = {
        '**%meme**':  'Get a random meme from reddit.',
        '**%translate  < Text to translate >**':  'Translate between text, binary, hexadecimal and chill++.',
        '**/search_reddit  < query >**':  'Search Reddit for posts based on a query.',
        '**/passwordgen  < password length >**':  'Generates a secure password and sends it privately through an ephemeral response.',
        '**/setup**':  'Set up the CRYPTCADA log channel. (Admin permissions required)',
        '**/ping**':  'Tells you the bots latency.',
        '**/invite**':  'Invite the bot to your own server.',
        '**/help**':  'Show this help message.'
    }

    # Create a formatted help message
    help_message = "***available commands:***\n\n"
    for command, description in commands_info.items():
        help_message += f"{command}:  {description}\n"

    # Send the help message to the user with code formatting
    await slash_embed_message(ctx, f"{help_message}", discord.Color.red())

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
