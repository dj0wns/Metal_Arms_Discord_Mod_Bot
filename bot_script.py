import discord
import asyncio
import random
import os
import datetime
import tempfile
import io
import operator
import re
import glob

import sqldb

fpath=os.path.realpath(__file__)
path=os.path.dirname(fpath)
DB_FILE=path+"/local.db"
datetime_format = '%Y-%m-%d %H:%M:%S'

attachments_channel_id=709879418348109837
guild_id=709849137251745963

async def checkArguments(channel, argsExpected, commandText, tokens):
  if len(tokens) < argsExpected:
    await channel.send(commandText + " requires at least " + str(argsExpected) + " argument" + ("s." if argsExpected > 1 else "."))  
    return False
  else:
    return True

def get_user(id):
    user = client.get_user(id)
    if user is None:
        user = "Unknown"
    else:
        user = user.name
    return user

async def commands(channel, author, client):
  #make rich embed
  message=( 
            " - !help - Displays this useful help dialog!\n"
            " - !set [mod_id] [name - 1 word only] [map_name - 1 word only] [description] - Sets the information for the given mod file\n"
            " - !upvote [mod_id] - Adds one upvote to the mod id - only 1 allowed per user per mod\n"
            " - !downvote [mod_id] - Adds one downvote to the mod id - only 1 allowed per user per mod\n"
            " - !stats [mod_id] - Prints all known data on the given mod id\n"
            " - !top - Lists the top 10 mods by votes\n"
          )
  how_to_upload=(
            "When you embed a zip file in the uploads the bot will respond with an id corresponding to that zip file. "
            "With that id you can use the set attributes function to give it a name, specify which map its for and then add a desctiption. "
            "These input fields can be used for other users to search for the mod. "

                )
  embedMessage = discord.Embed()
  embedMessage.add_field(name="General Commands", value=message, inline=False)
  embedMessage.add_field(name="How to Upload", value=how_to_upload, inline=False)
  await channel.send(embed=embedMessage)

async def set(channel, author, client, tokens):
  #TODO add check that only the uploader can change this information
  embed_id = tokens[1]
  name = tokens[2]
  map_name = tokens[3]
  description = ' '.join(tokens[4:])
  #First make sure this person is the owner
  f = sqldb.get_file(embed_id)
  if f is None:
    await channel.send("File not found!")
  else:
    if f[1] != author.id:
      await channel.send("You are not the owner of that file!")
    else:
      sqldb.update_file(embed_id, name, map_name, description)
      await channel.send(str(embed_id) + " successfully updated!")

async def upvote(channel, author, client, tokens):
  f = sqldb.get_file(tokens[1])
  if f is None:
    await channel.send("File not found!")
  else:
    sqldb.set_vote(tokens[1], author.id, 1)
    await channel.send("Upvote saved!")

async def downvote(channel, author, client, tokens):
  f = sqldb.get_file(tokens[1])
  if f is None:
    await channel.send("File not found!")
  else:
    sqldb.set_vote(tokens[1], author.id, -1)
    await channel.send("Downvote saved!")

async def stats(channel, author, client, tokens):
  f = sqldb.get_file(tokens[1])
  if f is None:
    await channel.send("File not found!")
  else:
    f_id = str(f[0])
    u_id = str(get_user(f[1]))
    file_name = str(f[2])
    name = str(f[3])
    map_name = str(f[4])
    description = str(f[5])
    time = str(f[6])
    downvotes = str(f[7])
    upvotes = str(f[8])
    link = "https://discordapp.com/channels/" + str(guild_id) + "/" + str(attachments_channel_id) + "/" + f_id
    embed_desc="[Link](" + link + ")\n" + description
    embedMessage = discord.Embed(title=name, description=embed_desc, color=0xe3f503)
    embedMessage.add_field(name="Uploader", value=u_id, inline=True)
    embedMessage.add_field(name="File Name", value=file_name, inline=True)
    embedMessage.add_field(name="Mod Type", value=map_name, inline=True)
    embedMessage.add_field(name="Upvotes", value=upvotes, inline=True)
    embedMessage.add_field(name="Downvotes", value=downvotes, inline=True)
    embedMessage.add_field(name="Upload Date", value=time, inline=True)
    await channel.send(embed=embedMessage)

async def top(channel, author, client, tokens):
  values = sqldb.get_top(10)
  embedMessage = discord.Embed(title="Top 10 Files", color=0xe3f503)
  for f in values:
    f_id = str(f[0])
    u_id = str(get_user(f[1]))
    file_name = str(f[2])
    name = str(f[3])
    map_name = str(f[4])
    description = str(f[5])
    time = str(f[6])
    score = str(f[7])
    link = "https://discordapp.com/channels/" + str(guild_id) + "/" + str(attachments_channel_id) + "/" + f_id
    message="[Link](" + link + ")\n" + "**Score:** " + score + "\n" + description + "\n**ID:** " + f_id
    embedMessage.add_field(name=name + " - " + map_name, value=message, inline=False)
  await channel.send(embed=embedMessage)
  return

async def delete(channel, author, client, tokens):
  if author.id != 179808295895302155: #dj0wns ID, no one else can delete anything
    await channel.send("You are not allowed to use this command.")
  else:
    sqldb.delete_item(tokens[1])
    await channel.send("Deleted file if it exists.")


async def parse_command(client,channel,author,name,content):
  if not content[0] == '!':
    return False
  #remove '!'
  message = content[1:]
  tokens = message.split()
  operation = tokens[0].lower()
  print(operation)
  if operation == "commands" or operation == "help":
    await commands(channel,author,client)
  elif operation == "set" and await checkArguments(channel, 3, operation, tokens):
    await set(channel, author, client, tokens)
  elif operation == "upvote" and await checkArguments(channel, 1, operation, tokens):
    await upvote(channel, author, client, tokens)
  elif operation == "downvote" and await checkArguments(channel, 1, operation, tokens):
    await downvote(channel, author, client, tokens)
  elif operation == "stats" and await checkArguments(channel, 1, operation, tokens):
    await stats(channel, author, client, tokens)
  elif operation == "top":
    await top(channel, author, client, tokens)
  elif operation == "delete" and await checkArguments(channel, 1, operation, tokens):
    await delete(channel, author, client, tokens)
    
    
  


#verify tables exist
sqldb.init_db()
token = open(path+"/token", "r").readline()
print(token)
client = discord.Client()

@client.event
async def on_ready(): #This runs once when connected
  print(f'We have logged in as {client.user}')
  await client.change_presence(activity=discord.Game(name="Duping Cleaners"))

@client.event
async def on_message(message):
  #Don't respond to self
  if not message.author == client.user:
    #try:
      if message.attachments and message.channel.id == attachments_channel_id:
        #check to make sure its a zip file
        attach_name = message.attachments[0].filename
        name, extension = os.path.splitext(attach_name)
        if extension.lower() == ".zip":
            new_id = sqldb.create_file(message.author.id, message.id, attach_name)
            await message.channel.send("New mod uploaded with id of: " + str(new_id[0]))
      if len(message.content) > 0:
        await parse_command(client,message.channel,message.author,message.author.display_name,message.content)
    #except Exception as e:
      #print(e)
      #await message.channel.send("Exception raised: '" + str(e) + "'\n - Pester dj0wns that his bot is broken on this command")
      
  print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")

client.run(token)

