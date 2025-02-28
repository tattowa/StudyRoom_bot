import discord
from discord.ext import commands, tasks
from datetime import datetime

class RoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.study_sessions = {}
        self.update_nicknames.start()  # 定期的にニックネームを更新するタスクを開始

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        study_role = discord.utils.get(member.guild.roles, name="勉強中")
        
        if after.channel:
            await member.add_roles(study_role)
            self.study_sessions[member.id] = datetime.now()
        elif before.channel and not after.channel:
            await member.remove_roles(study_role)
            if member.id in self.study_sessions:
                start_time = self.study_sessions.pop(member.id)
                duration = (datetime.now() - start_time).total_seconds() / 60
                df_logs = self.bot.get_cog('StudyTimeTracker').load_data()
                df_sessions = self.bot.get_cog('StudyTimeTracker').calculate_study_sessions(df_logs)
                title = self.bot.get_cog('StudyTimeTracker').assign_title(df_sessions, member.id)
                await self.update_nickname(member, title, duration)

    @tasks.loop(minutes=1)  # 1分ごとに定期的に実行
    async def update_nicknames(self):
        # "勉強中"ロールが付与されているメンバーに対して
        study_role = discord.utils.get(self.bot.guilds[0].roles, name="勉強中")
        for member in study_role.members:
            if member.id in self.study_sessions:
                start_time = self.study_sessions[member.id]
                duration = (datetime.now() - start_time).total_seconds() / 60
                df_logs = self.bot.get_cog('StudyTimeTracker').load_data()
                df_sessions = self.bot.get_cog('StudyTimeTracker').calculate_study_sessions(df_logs)
                title = self.bot.get_cog('StudyTimeTracker').assign_title(df_sessions, member.id)
                await self.update_nickname(member, title, duration)

    async def update_nickname(self, member, title, duration):
        # ニックネームを更新
        if title == "Master":
            await member.edit(nick=f"{member.display_name}{title}@{int(duration)}分勉強中")
        elif title == "Expert":
            await member.edit(nick=f"{member.display_name}{title}@{int(duration)}分勉強中")
        else:
            await member.edit(nick=f"{member.display_name}{title}")

    @update_nicknames.before_loop
    async def before_update_nicknames(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(RoleManager(bot))
