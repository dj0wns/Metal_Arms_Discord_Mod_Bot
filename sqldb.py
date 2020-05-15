import sqlite3
import discord
import asyncio
import random
import os
import datetime
import tempfile
import io
import operator
import glob
from sqlite3 import Error

fpath=os.path.realpath(__file__)
path=os.path.dirname(fpath)
DB_FILE=path+"/local.db"

auction_mode = False
auction_item = ""
auction_dict = {}


# Initializes tables and some data in the database if they don't exist
def init_db():
  sql_commands = []
  sql_commands.append("PRAGMA foreign_keys = ON;")
  sql_commands.append(""" CREATE TABLE IF NOT EXISTS files (
                            embed_id integer NOT NULL PRIMARY KEY,
                            discord_id integer NOT NULL,
                            file_name text NOT NULL,
                            name text UNIQUE DEFAULT NULL,
                            map text DEFAULT NULL,
                            description text DEFAULT NULL,
                            uploaded_at datetime DEFAULT CURRENT_TIMESTAMP
                          ) WITHOUT ROWID; """)
  sql_commands.append(""" CREATE TABLE IF NOT EXISTS votes (
                            id integer NOT NULL PRIMARY KEY,
                            embed_id integer NOT NULL,
                            discord_id integer NOT NULL,
                            value integer NOT NULL,
                            CONSTRAINT fk_embed_id FOREIGN KEY(embed_id) REFERENCES files(embed_id) ON DELETE CASCADE,
                            UNIQUE(embed_id, discord_id)
                          )""")
  try:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for sql_command in sql_commands:
      c.execute(sql_command)
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()


### PLAYER SQL FUNCTIONS ###

# given a db connection, creates player in db if they don't already exist
def create_file(discord_id, embed_id, file_name):
  sql = """ INSERT OR IGNORE INTO files(discord_id, embed_id, file_name)
              VALUES(?, ?, ?) """
  ret_query = "SELECT embed_id FROM files WHERE embed_id=?"
  to_insert = (discord_id, embed_id, file_name)
  to_ret = (embed_id,)
  try:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(sql, to_insert)
    conn.commit()
    c.execute(ret_query, to_ret)
    ret = c.fetchone()
    #else do nothing
    return ret
  except Error as e:
    print(e)
  finally:
    conn = conn.close()

def get_file(embed_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM files WHERE embed_id=?", (embed_id,))
    ret = c.fetchone()
    if ret is None:
      return None
    retlist = list(ret)

    c.execute("SELECT count(*) FROM votes WHERE embed_id=? and value<0", (embed_id,))
    retlist.append(c.fetchone()[0])
    c.execute("SELECT count(*) FROM votes WHERE embed_id=? and value>0", (embed_id,))
    retlist.append(c.fetchone()[0])
    return retlist
  except Error as e:
    print(e)
  finally:
    conn.close()


def update_file(embed_id, name, map_name, description):
  try:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE files SET name=?, map=?, description=? WHERE embed_id=?", (name, map_name, description, embed_id,))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()

def set_vote(embed_id, player_id, value):
  try:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO votes (id, embed_id, discord_id, value)"
              " VALUES ((SELECT id FROM votes where embed_id=? AND discord_id=?),?,?,?)",
              (embed_id, player_id, embed_id, player_id, value))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()

def get_top(count):
  query ="""SELECT files.*, IFNULL(sum(votes.value),0) as sum_of_votes
            from files
            left join votes
            on (files.embed_id = votes.embed_id)
            group by files.embed_id
            ORDER by sum_of_votes DESC
            LIMIT ?;
         """
  try:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, (count,))
    return c.fetchall()
  except Error as e:
    print(e)
  finally:
    conn.close()

def delete_item(f_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM files where embed_id=?", (f_id,))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()

