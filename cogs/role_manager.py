import discord
from discord.ext import commands
from datetime import datetime

class RoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.study_sessions = {}

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        study_role = discord.utils.get(member.guild.roles, name="勉強中")
        master_role = discord.utils.get(member.guild.roles, name="Master")
        expert_role = discord.utils.get(member.guild.roles, name="Expert")
        beginner_role = discord.utils.get(member.guild.roles, name="Beginner")

        if after.channel:
            await member.add_roles(study_role)
            self.study_sessions[member.id] = datetime.now()
        elif before.channel and not after.channel:
            await member.remove_roles(study_role)
            if member.id in self.study_sessions:
                start_time = self.study_sessions.pop(member.id)
                duration = (datetime.now() - start_time).total_seconds() / 60
                # 称号を取得
                df_logs = self.bot.get_cog('StudyTimeTracker').load_data()
                df_sessions = self.bot.get_cog('StudyTimeTracker').calculate_study_sessions(df_logs)
                title = self.bot.get_cog('StudyTimeTracker').assign_title(df_sessions, member.id)
                # ニックネームを更新
                if after.channel:
                    await member.edit(nick=f"{member.display_name}{title}@{int(duration)}分勉強中")
                else:
                    await member.edit(nick=f"{member.display_name}{title}")
                # 既存の称号ロールを削除
                await member.remove_roles(master_role, expert_role, beginner_role)
                # 新しい称号ロールを付与
                if title == "Master":
                    await member.add_roles(master_role)
                    await master_role.edit(colour=discord.Colour.gold())
                elif title == "Expert":
                    await member.add_roles(expert_role)
                    await expert_role.edit(colour=discord.Colour.blue())
                else:
                    await member.add_roles(beginner_role)
                    await beginner_role.edit(colour=discord.Colour.green())

async def setup(bot):
    await bot.add_cog(RoleManager(bot))