import discord
from discord.ext import commands

class RoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        role = discord.utils.get(member.guild.roles, name="勉強中")
        if after.channel:
            await member.add_roles(role)
        elif before.channel and not after.channel:
            await member.remove_roles(role)

async def setup(bot):
    await bot.add_cog(RoleManager(bot))