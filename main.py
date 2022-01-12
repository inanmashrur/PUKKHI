import discord
from discord.ext import commands
import os

from youtube_dl import YoutubeDL
#for running in the server
from keep_alive import keep_alive
#for lyrics
from lyricsgenius import Genius
genius = Genius(os.getenv('LG_TOKEN'))

'''
'''

bot = commands.Bot(command_prefix='?')

is_playing = False
is_loop = False
m_url = ""
music_queue = [] # 2d array containing [song, channel]
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
vc = []
current_song = []

#defined functions
#---------------------
#searching the item on youtube
def search_yt(item):
  with YoutubeDL(YDL_OPTIONS) as ydl:
    try:
      info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
    except Exception:
      return False

  return {'source': info['formats'][0]['url'], 'title': info['title']}

def check(text):
  print(text)
  for i in range(0,len(music_queue)):
    print(music_queue[i][0]['title'])
  print("\n\n")

# infinite loop checking
async def play_music():
  global is_playing
  global is_loop
  global current_song
  global m_url

  if len(music_queue) > 0 and not is_playing:
    m_url = music_queue[0][0]['source']



    #try to connect to voice channel if you are not already connected
    if len(vc)==0 :
      vc.append(await music_queue[0][1].connect())

    #print("VC: ",vc)
    check("before pop")
    current_song = music_queue.pop(0)
    check("after pop")

    if is_loop:
      music_queue.append([current_song[0], current_song[1]])
      check("pop loop")

    is_playing = True

    vc[0].play(discord.FFmpegPCMAudio(m_url, **FFMPEG_OPTIONS), after=lambda e: play_next())
  else:
    is_playing = False
    music_queue.clear()
    current_song.clear()

#play next song
def play_next():
  global is_playing
  global is_loop
  global current_song
  global m_url

  if len(music_queue) > 0:
    is_playing = True

    #get the first url
    m_url = music_queue[0][0]['source']

    check("next before pop")
    current_song = music_queue.pop(0)
    check("next after pop")

    if is_loop:
      music_queue.append([current_song[0], current_song[1]])
      check("next pop loop")

    vc[0].play(discord.FFmpegPCMAudio(m_url, **FFMPEG_OPTIONS), after=lambda e: play_next())
  else:
    is_playing = False
    music_queue.clear()
    current_song.clear()

async def clear(channel, arg):
  #extract the amount to clear
  amount = 5
  try:
    amount = int(arg)
  except Exception: pass
  print("in clear")
  await channel.purge(limit=amount)
  await channel.send("""```""" +str(amount)+ " text was cleared !" +"""```""")
  await channel.purge(limit=1)

async def add_a_song(query, voice_channel, text_channel):
  song = search_yt(query)
  print(song)

  if type(song) == type(True):
    await text_channel.send("""```"""+query+" could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format."+"""```""")

  else:
    await text_channel.send("""```"""+song['title']+" talikay jog kore diyechi"+"""```""")
    music_queue.append([song, voice_channel.channel])

async def add_songs(playlist, voice_channel, text_channel):

  for i in range(0,len(playlist)):
    query = playlist[i]
    song = search_yt(query)
    print(song)

    if type(song) == type(True):
      await text_channel.send("""```"""+query+" could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format."+"""```""")
    else:
      music_queue.append([song, voice_channel.channel])

  await text_channel.send("""```"""+"talika peyechi!"+"""```""")
#----------------------------------

#execute commands
#----------------------------------
#----------------------------------
async def on_call(message):
  global is_playing
  global is_loop
  global current_song

  print("inside on call")
  msg = ""
  author_name = message.author.name
  author_discriminator = message.author.discriminator
  voice_channel = message.author.voice
  text_channel = message.channel

  if message.content.startswith('pukkhi '):
    msg = message.content.replace('pukkhi ','')

  else:
    msg = message.content.replace('.p ','')

  if msg.startswith('hey'):
    await text_channel.send('Hey @'+author_name+"#"+author_discriminator+',  pukkhi is here')

  elif msg.startswith('acho'):
    await text_channel.send('achito '+author_name+" babu :* ")

  elif msg.startswith('about'):
    await text_channel.send("""```"""+'Kire, '+author_name+' mama! pukkhire chino na? dudhu khao?'+"""```""")

  elif msg.startswith('gao'):
    query = msg.replace('gao ','')

    if voice_channel is None:
      #you need to be connected so that the bot knows where to go
      await text_channel.send("""```""" +"voice channel ae join de madari!"+"""```""")

    else:
      await add_a_song(query, voice_channel, text_channel)

      if is_playing == False:
          await play_music()

  elif msg.startswith('bodlao'):
    print("\nbodlao\n")

    if len(vc)>0:
      #print("\nin if\n")
      vc[0].stop()
      if len(music_queue)==0:
        await text_channel.send("""```""" +"Queue khali-koira gaan gaite bolo? gelam ga!"+"""```""")
        await vc[0].disconnect()
        vc.clear()
        is_playing = False
        music_queue.clear()
        current_song.clear()
      #try to play next in the queue if it exists
      else:
        await text_channel.send("""```""" +"ekhon gaibo:\n"+music_queue[0][0]['title']+"""```""")
        play_next()

  elif msg.startswith('thamo'):
    print("\nthamo\n")

    if len(vc)>0:
      vc[0].pause()
      await text_channel.send("""```""" +current_song[0]['title']+" gaoya thamailam, shunte chaile boilo abar!"+"""```""")

  elif msg.startswith('abar'):
    print("\nabar\n")

    if len(vc)>0:
      vc[0].resume()
      await text_channel.send("""```""" +current_song[0]['title']+" gaoya shurur korlam abar!"+"""```""")
      #try to play next in the queue if it exists
      await play_next()

  elif msg.startswith('talika'):

    if len(music_queue)==0:
      await text_channel.send("""```""" +"talika khali to baal!!!!"+"""```""")

    else:
      song_list = "talikay ache:\n"

      for i in range(0,len(music_queue)):
        song_list+= str(i+1)+". "+str(music_queue[i][0]['title'])+"\n"

      await text_channel.send("""```""" +song_list+"""```""" )

  elif msg.startswith('playlist'):
    music_queue.clear()
    print(msg)
    playlist = msg.replace('playlist ','')
    print(playlist)
    temp = playlist.split("##")

    print(temp)

    is_loop = False
    if len(temp)==2:
      if temp[1] == "cokro":
        is_loop = True
        await text_channel.send("""```Cokro biddoman!```""")
    playlist = temp[0].split('+')

    print(playlist)

    await add_songs(playlist, voice_channel, text_channel)

    if is_playing == False:
      await play_music()

  elif msg.startswith('lyric'):

    song_name = msg.replace('lyric ','')

    if song_name == "lyric":
      await text_channel.send("""```""" +"gaan er naam diba na naki?"+"""```""")
      return

    await text_channel.send("""```""" +"khujtechi.........."+"""```""")

    song = genius.search_song(title=song_name)

    try:

      lyrics = song.lyrics
      lyrics = """```""" + lyrics.replace('EmbedShare URLCopyEmbedCopy','')+"""```"""
      await text_channel.send(lyrics)
      print("lyrics found")

    except:
      await text_channel.send("""```""" +"kono lyric e khuija pailam na!"+"""```""")
      print(">> lyrics were not found")

  elif msg.startswith('cokro'):
    print("\nchokro\n")
    is_loop = not is_loop
    if is_loop:
      if len(music_queue)==0:
        music_queue.append([current_song[0], current_song[1]])
      await text_channel.send("""```""" +"kaamla lagi to tomar?"+"""```""")
    else:
      await text_channel.send("""```""" +"ei j line e asla mama!"+"""```""")

  elif msg.startswith('chole jao'):
    print("\nchole jao\n")
    if len(vc)>0:
      #print("\nin if\n")
      await text_channel.send("""```""" + author_name+" see you never! :)"+"""```""")
      await vc[0].disconnect()
      vc.clear()
      is_playing = False
      music_queue.clear()

  elif msg.startswith('clear') and (author_name+author_discriminator)=="BlackLight7447":
    arg = msg.replace('clear ','')
    await clear(text_channel,arg)
    print(author_name+author_discriminator)

  elif msg.startswith('bachao'):
    help = """```""" + "\nde de hukum de madari\n-------------------------------------\nhey\nacho :: thakle awaj dibo\nabout :: amar sompor k jante parbe\ngao songname :: ganti gaoyar ceshta korbo\nbodlao :: poriborton kore poroborti gaan gaibo\nthamo :: gaan gaoya thamiye dibo\nabar ::  abar gabo gaan\ntalika :: ki gan gaibo janabo\nlyric :: gaoya gantir gitiKabbo khuje dibo\ncokro :: bajatei thakbo othoba ekbar e bajabo\nplaylist song1+song2+.._songN ##cokro :: sompurno talikati bajabo or bajatei thakbo ##cokro dile\nping :: koto deri parjeri- dekhabo\nchole jao :: chole jete bolbe amay?\nbachao :: kivabe bachate pari janabo\n"+"""```"""

    await text_channel.send(help)

  elif msg.startswith('ping'):
    await text_channel.send(f'**Pong!** Latency: {round(bot.latency * 1000)}ms')

  else:
    return

#----------------------------------
#----------------------------------


#events
@bot.event
async def on_ready():
  print('Hello {0.user}'.format(bot),"is online")

@bot.event
async def on_message(message):

  if message.author == bot.user:
    return

  if message.content.startswith("pukkhi") or message.content.startswith(".p"):
    print("called")
    await on_call(message)

  else:
    return


keep_alive()
bot.run(os.getenv('TOKEN'))

'''
python3 -m pip install -U discord.py[voice]

'''
