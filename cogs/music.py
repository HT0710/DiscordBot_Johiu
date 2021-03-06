import asyncio
import youtube_dl
import discord
from discord.ext import commands

client = commands.Bot(command_prefix=';', intents=discord.Intents.all(), help_command=None)


class Music(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.channel_id = 0
        self.song_queue = {}
        self.current = {}
        self.loop = {}
        self.setup()

    def setup(self):
        for guild in self.client.guilds:
            self.song_queue[guild.id] = []
            self.current[guild.id] = {}
            self.loop[guild.id] = {}

    async def hyphen(self, ctx, sub):  # khi sub.find('-') trả về -1 (False)
        sub = sub.split('-')  # tách thành list

        try:  # check có nhập đúng int hay ko
            for i in range(len(sub)):  # biến list str thành list int
                sub[i] = int(sub[i])

            sub.sort()  # chắc chắn a < b

            if len(sub) > 2:  # check nhập đúng a-b hay ko, list phai == 2 ['a', 'b']
                await ctx.send('Nhập cho đúng chứ. Lệnh **`help`** để biết thêm')

            else:
                for i in range(sub[0] - 1, sub[1]):  # bắt đầu, chạy từ a-1 đến b(b đã tự -1), -1 vì list tính từ 0
                    self.song_queue[ctx.guild.id].pop(
                        sub[0] - 1)  # xóa ở vị trí (a-1) (b) lần vì mỗi lần xóa thứ tự đôn lên
        except:
            await ctx.send('Nhập cho đúng chứ. Lệnh **`help`** để biết thêm')  # lỗi nhập chữ, không int đc,...

    async def comma(self, ctx, sub):
        sub = sub.split(',')  # tách thành list

        try:  # check có nhập đúng hay ko
            for i in range(len(sub)):  # biến list str thành list int
                sub[i] = int(sub[i])

            copy = self.song_queue[
                ctx.guild.id].copy()  # tạo một bản copy vì length sẽ thay đổi khi pop thành ra lỗi (cách tạm thời)

            sub.sort()  # sắp xếp a cho dễ pop

            sub = list(dict.fromkeys(sub))  # loại bỏ trùng lặp

            for i in reversed(range(len(sub))):  # chạy trong length a từ lớn đến bé tránh khi pop bị đôn lên
                for j in range(len(copy)):  # chạy hết length bản copy
                    if sub[i] - 1 == j:
                        self.song_queue[ctx.guild.id].pop(j)
        except:
            await ctx.send('Nhập cho đúng chứ. Lệnh **`help`** để biết thêm')  # lỗi nhập chữ, không int đc,...

    async def check_queue(self, ctx):
        if len(self.song_queue[ctx.guild.id]) > 0 or self.loop[self.channel_id]['q'] == 'True':
            if self.loop[self.channel_id]['q'] == 'False':
                await self.play_song(ctx, self.song_queue[ctx.guild.id][0]['d'])
                await self.client.get_channel(self.channel_id).send(
                    f"Now playing: {self.song_queue[ctx.guild.id][0]['d']}")
                self.song_queue[ctx.guild.id].pop(0)
            else:
                self.song_queue[ctx.guild.id].append(
                    {'s': self.current[self.channel_id]['s'], 'd': self.current[self.channel_id]['d']})
                await self.play_song(ctx, self.song_queue[ctx.guild.id][0]['d'])
                await self.client.get_channel(self.channel_id).send(
                    f"Now playing: {self.song_queue[ctx.guild.id][0]['d']}")
                self.song_queue[ctx.guild.id].pop(0)

    async def search_song(self, amount, song, get_url=False):
        info = await self.client.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL(
            {"format": "bestaudio", "quiet": True}).extract_info(f"ytsearch{amount}:{song}", download=False,
                                                                 ie_key="YoutubeSearch"))
        if len(info["entries"]) == 0: return None

        return [entry["webpage_url"] for entry in info["entries"]] if get_url else info

    async def play_song(self, ctx, url):
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                          'options': '-vn'}
        YDL_OPTIONS = {'format': 'bestaudio'}

        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
            ctx.guild.voice_client.play(source)
            self.current[self.channel_id] = {'s': info['title'], 'd': url}

    @commands.command()
    async def test(self, ctx, sub=None):
        return await ctx.send(self.channel_id)

    @commands.command()
    async def join(self, ctx):
        await ctx.author.voice.channel.connect()

    @commands.command(aliases=['play', 'p'])
    async def jplay(self, ctx, *, song=None):
        await ctx.message.add_reaction('▶️')
        try:
            if ctx.author.voice is None:
                await ctx.send('Chui vào voice đi cái đã')
                return
            voice_channel = ctx.author.voice.channel
            if ctx.voice_client is None:
                await voice_channel.connect()
            else:
                await ctx.voice_client.move_to(voice_channel)
        except:
            pass

        # handle song where song isn't url
        if not ("youtube.com/watch?" in song or "https://youtu.be/" in song):
            await ctx.send("Đang tìm kiếm... mất một vài giây.")

            result = await self.search_song(1, song, get_url=True)

            if result is None:
                return await ctx.send("Không tìm thấy kết quả, hãy thử dùng lệnh **search**.")

            song = result[0]

        # check any song is playing
        queue_len = len(self.song_queue[ctx.guild.id])
        if ctx.voice_client.is_playing():
            info = youtube_dl.YoutubeDL().extract_info(song, download=False)
            self.song_queue[ctx.guild.id].append({'s': info['title'], 'd': song})
            return await ctx.send(
                f"Hiện có bài đang phát, sẽ được thêm vào danh sách phát ở vị trí: **`{queue_len + 1}`**.")

        self.channel_id = ctx.channel.id
        self.loop[self.channel_id] = {'1': '', 'q': ''}
        self.loop[self.channel_id]['1'] = 'False'
        self.loop[self.channel_id]['q'] = 'False'
        await self.play_song(ctx, song)
        await ctx.send(f'Now playing {song}')

    @commands.command(aliases=['fplay', 'fp'])
    async def jforceplay(self, ctx, *, song):
        await ctx.message.add_reaction('▶️')
        try:
            if ctx.author.voice is None:
                await ctx.send('Chui vào voice đi cái đã')
                return
            voice_channel = ctx.author.voice.channel
            if ctx.voice_client is None:
                await voice_channel.connect()
            else:
                await ctx.voice_client.move_to(voice_channel)
        except:
            pass

        # handle song where song isn't url
        if not ("youtube.com/watch?" in song or "https://youtu.be/" in song):
            await ctx.send("Đang tìm kiếm... mất một vài giây.")

            result = await self.search_song(1, song, get_url=True)

            if result is None:
                return await ctx.send("Không tìm thấy kết quả, hãy thử dùng lệnh **search**.")

            song = result[0]

        ctx.voice_client.stop()
        self.loop[self.channel_id]['1'] = 'False'
        await self.play_song(ctx, song)
        await ctx.send(f'Now playing {song}')

    @commands.command(aliases=['leave', 'l'])
    async def jleave(self, ctx):
        if ctx.voice_client is not None:
            await ctx.message.add_reaction('🆗')
            self.current[self.channel_id] = {}
            return await ctx.voice_client.disconnect()

        await ctx.send("Có đang ở trong voice đâu?.")

    @commands.command(aliases=['pause', 's'])
    async def jpause(self, ctx):
        if ctx.voice_client.is_paused():
            return await ctx.send("Đang dừng rồi mà?")

        ctx.voice_client.pause()
        await ctx.message.add_reaction('🆗')
        await ctx.send("Đã tạm dừng ⏸️")

    @commands.command(aliases=['resume', 'r'])
    async def jresume(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("Đã ở trong voice đâu?")

        if not ctx.voice_client.is_paused():
            return await ctx.send("Vẫn đang play mà?")

        ctx.voice_client.resume()
        await ctx.message.add_reaction('🆗')
        await ctx.send("Bài hát hiện tại đã được tiếp tục ▶️")

    @commands.command(aliases=['loop', 'o'])
    async def jloop(self, ctx, sub=None):
        if ctx.voice_client is None:
            return await ctx.send("Đã ở trong voice đâu?")

        if sub is None:
            if self.loop[self.channel_id]['1'] == 'False':
                await ctx.send('Hiện loop đang **`Tắt\off`**')
            else:
                await ctx.send(f"Hiện loop đang **`Bật\on`**")
        else:
            if sub == 'on':
                await ctx.message.add_reaction('🔂')
                self.loop[self.channel_id]['1'] = 'True'
                embed = discord.Embed(title=f"Bắt đầu loop! - [{self.current[self.channel_id]['s']}]({self.current[self.channel_id]['d']})", colour=discord.Colour.purple())
                return await ctx.send(embed=embed)
            elif sub == 'off':
                await ctx.message.add_reaction('❌')
                self.loop[self.channel_id]['1'] = 'False'
                embed = discord.Embed(title='Đã dừng loop!', colour=discord.Colour.dark_purple())
                return await ctx.send(embed=embed)
            else:
                return await ctx.send("Sai lệnh! Thử lại xem")

    @commands.command(aliases=['qloop', 'qo'])
    async def jqueueloop(self, ctx, sub=None):
        if ctx.voice_client is None:
            return await ctx.send("Đã ở trong voice đâu?")

        if sub is None:
            if self.loop[self.channel_id]['q'] == 'False':
                await ctx.send('Hiện queue loop đang **`Tắt\off`**')
            else:
                await ctx.send('Hiện queue loop đang **`Bật\on`**')
        else:
            if sub == 'on':
                await ctx.message.add_reaction('🔁')
                self.loop[self.channel_id]['q'] = 'True'
                embed = discord.Embed(title='Bắt đầu loop...', colour=discord.Colour.purple())
                return await ctx.send(embed=embed)
            elif sub == 'off':
                await ctx.message.add_reaction('❌')
                self.loop[self.channel_id]['q'] = 'False'
                embed = discord.Embed(title='Đã dừng loop!', colour=discord.Colour.dark_purple())
                return await ctx.send(embed=embed)
            else:
                return await ctx.send("Sai lệnh! Thử lại xem")

    @commands.command(aliases=['nowplaying', 'n'])
    async def jnowplaying(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("Đã ở trong voice đâu?")
        if ctx.guild.voice_client.is_playing() is False:
            return await ctx.send("Có đang play gì đâu?")

        await ctx.message.add_reaction('🆗')
        await ctx.send(f"Đang phát hiện tại: [{self.current[self.channel_id]['s']}]({self.current[self.channel_id]['d']})")

    @commands.command(aliases=['search', 'f'])
    async def jsearch(self, ctx, *, song=None):
        if song is None:
            return await ctx.send("Search gì mới được.")

        await ctx.message.add_reaction('🆗')
        await ctx.send("Đang tìm kiếm... mất một vài giây.")

        info = await self.search_song(5, song)

        embed = discord.Embed(title=f"Kết quả cho '{song}':",
                              description="*Lấy link(url) trực tiếp từ tên bài hát nếu không phải là bài đầu tiên.*\n",
                              colour=discord.Colour.red())

        amount = 0
        for entry in info["entries"]:
            embed.description += f"[{entry['title']}]({entry['webpage_url']})\n"
            amount += 1

        embed.set_footer(text=f"{amount} kết quả đầu tiên tìm được.")
        await ctx.send(embed=embed)

    @commands.command(aliases=['skip', 'k'])
    async def jskip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("Đã ở trong voice nào đâu?")

        if ctx.author.voice is None:
            return await ctx.send("Vào voice đi cái đã.")

        if ctx.guild.voice_client.is_playing() is False:
            return await ctx.send("Có đang play gì đâu mà skip?")

        await ctx.message.add_reaction('🆗')
        poll = discord.Embed(title=f"Vote to Skip Song by - {ctx.author.name}#{ctx.author.discriminator}",
                             description="**__60%__ của voice channel đồng ý để skip.**",
                             colour=discord.Colour.blue())
        poll.add_field(name="Skip", value=":white_check_mark:")
        poll.add_field(name="Stay", value=":no_entry_sign:")
        poll.set_footer(text="Vote kết thúc trong 10 giây.")

        poll_msg = await ctx.send(
            embed=poll)  # only returns temporary message, we need to get the cached message to get the reactions
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705")  # yes
        await poll_msg.add_reaction(u"\U0001F6AB")  # no

        await asyncio.sleep(10)  # 10 seconds to vote

        poll_msg = await ctx.channel.fetch_message(poll_id)

        votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        reacted = []

        for reaction in poll_msg.reactions:
            if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                async for user in reaction.users():
                    if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                        votes[reaction.emoji] += 1

                        reacted.append(user.id)

        skip = False

        if votes[u"\u2705"] > 0:
            if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (
                    votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.59:  # 60% or higher
                skip = True
                embed = discord.Embed(title="Skip ***Thành công***",
                                      description="***Chuyển bài ngay bây giờ...***",
                                      colour=discord.Colour.green())

        if not skip:
            embed = discord.Embed(title="Skip ***Thất bại***",
                                  description="***Cần ít nhất __60%__ phiếu đồng ý để skip.***",
                                  colour=discord.Colour.red())

        embed.set_footer(text="Vote kết thúc.")

        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=embed)

        if skip:
            ctx.voice_client.stop()
            self.loop[self.channel_id]['1'] = 'False'
            await self.check_queue(ctx)

    @commands.command(aliases=['queue', 'q'])
    async def jqueue(self, ctx):  # display the current guilds queue
        try:
            if len(self.song_queue[ctx.guild.id]) == 0 and self.current[self.channel_id] == {}:
                return await ctx.send("Không có bài nào trong danh sách hiện tại cả.")
        except:
            return await ctx.send("Không có bài nào trong danh sách hiện tại cả.")

        await ctx.message.add_reaction('🆗')

        end = '' if len(self.song_queue[ctx.guild.id]) == 0 else '-----Next-----\n'

        embed = discord.Embed(title="Danh sách phát",
                              description=f"**`Now playing`** 🔸 [{self.current[self.channel_id]['s']}]({self.current[self.channel_id]['d']}) 🔹\n{end}",
                              colour=discord.Colour.dark_gold())

        i = 1
        for info in self.song_queue[ctx.guild.id]:
            embed.description += f"**{i}** > [{info['s']}]({info['d']})\n"
            i += 1

        embed.add_field(name='Lặp một bài ',
                        value=f'{"**`Tắt/off`** ❌" if self.loop[self.channel_id]["1"] == "False" else "**`Bật/on`** 🔂"}',
                        inline=True)
        embed.add_field(name=' Lặp danh sách phát',
                        value=f'{"**`Tắt/off`** ❌" if self.loop[self.channel_id]["q"] == "False" else "**`Bật/on`** 🔁"}',
                        inline=True)
        embed.set_footer(text=f"Số lượng: [ {len(self.song_queue[ctx.guild.id])} ]")
        await ctx.send(embed=embed)

    @commands.command(aliases=['clean_queue', 'cq'])
    async def jclean_queue(self, ctx, *, sub=None):
        if sub is None:
            embed = discord.Embed(title='Hướng dẫn dùng clean queue',
                                  description='- Prefix: **`;`**',
                                  colour=discord.Color.blue())
            embed.description += '\n- **`cq all`**: xóa toàn bộ danh sách hiện tại'
            embed.description += '\n- **`cq [stt]`**: xóa bài hát cụ thể theo stt trong queue'
            embed.description += '\n- **`cq [a-b]`**: xóa các bài trong khoảng từ a tới b'
            embed.description += '\n- **`cq [a,b,c,...]`**: xóa các bài riêng lẻ a, b, c,...'
            return await ctx.send(embed=embed)

        if self.song_queue[ctx.guild.id] == []:
            return await ctx.send('Không có gì để xóa cả')

        await ctx.message.add_reaction('🆗')
        hyp = sub.find('-')  # doan
        com = sub.find(',')  # rieng le

        if sub == 'all':
            self.song_queue[ctx.guild.id].clear()
            return await ctx.send('Đã xóa toàn bộ thành công')

        elif hyp > 0:
            await self.hyphen(ctx, sub)
            return await ctx.send('Đã xóa đoạn thành công')

        elif com > 0:
            await self.comma(ctx, sub)
            return await ctx.send('Đã xóa các bài thành công')
        else:
            try:  # check có nhập đúng hay ko
                self.song_queue[ctx.guild.id].pop(int(sub) - 1)  # pop ở đúng vị trí đó -1 vì list đi từ 0
                return await ctx.send('Đã xóa bài hát thành công')

            except:
                await ctx.send('Nhập cho đúng chứ. Lệnh **`help`** để biết thêm')  # lỗi nhập chữ, không int đc,...

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id != self.client.user.id:
            return

        elif before.channel is None:
            voice = after.channel.guild.voice_client
            while True:
                while True:
                    await asyncio.sleep(8)
                    if (voice.is_playing() is False) and (voice.is_paused() is True):
                        a = 0
                        for i in range(900):
                            await asyncio.sleep(1)
                            if voice.is_playing():
                                a = 1
                                break
                        if a == 1:
                            continue
                        else:
                            voice = after.channel.guild.voice_client
                            await voice.disconnect()
                            self.current[self.channel_id] = {}
                            break
                    elif (voice.is_playing() is False) and (voice.is_paused() is False):
                        if self.loop[self.channel_id]['1'] == 'True':
                            await self.play_song(member, self.current[self.channel_id]['d'])
                            await self.client.get_channel(self.channel_id).send(
                                f"Now playing: {self.current[self.channel_id]['d']}")

                        elif len(self.song_queue[member.guild.id]) > 0 or self.loop[self.channel_id]['q'] == 'True':
                            await self.check_queue(member)

                        else:
                            await asyncio.sleep(2)
                            self.current[self.channel_id] = {}
                            b = 0
                            for i in range(300):
                                await asyncio.sleep(1)
                                if len(self.song_queue[member.guild.id]) > 0 or (voice.is_playing()):
                                    b = 1
                                    break
                            if b == 1:
                                continue
                            else:
                                await voice.disconnect()
                                break

                    if not voice.is_connected:
                        break
