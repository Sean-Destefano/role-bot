import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.reactions = True
intents.guild_reactions = True
intents.message_content = True

role_message_id = 1211496570491772938  # hardcoded for testing
emoji_role_map = {}

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(
    name="post_initial_message",
    description="Post the initial message for role-channel mapping",
)
async def post_initial_message(
    interaction: discord.Interaction, channel_id: str, content: str
):
    try:
        channel_id = int(channel_id)
    except ValueError:
        await interaction.response.send_message(
            "Invalid channel ID. Please enter a valid integer."
        )
        return

    channel = interaction.guild.get_channel(channel_id)
    if channel is None:
        await interaction.response.send_message("Invalid channel ID.")
        return

    message = await channel.send(content)
    global role_message_id
    role_message_id = message.id

    await interaction.response.send_message(
        f"Initial message posted in {channel.mention}. Message ID: {message.id}"
    )


@tree.command(
    name="create_role_channel",
    description="Create a role, set it as a reaction role, and create a channel for it",
)
async def create_role_channel(
    interaction: discord.Interaction, role_name: str, emoji: str
):
    guild = interaction.guild
    role = await guild.create_role(name=role_name)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        role: discord.PermissionOverwrite(read_messages=True),
    }
    channel = await guild.create_text_channel(role_name, overwrites=overwrites)

    if role_message_id is not None:
        channel_to_fetch = interaction.client.get_channel(
            1211399581611335742
        )  # hardcoded for testing
        message = await channel_to_fetch.fetch_message(role_message_id)
        new_content = f"{message.content}\n{role_name}: {emoji}"
        await message.edit(content=new_content)
        await message.add_reaction(emoji)
        global emoji_role_map
        emoji_role_map[emoji] = role.id
    await interaction.response.send_message(
        f"Created role {role.name} and channel {channel.name}. React to the message with {emoji} to get access."
    )


@client.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    emoji = str(reaction.emoji)
    role_id = emoji_role_map.get(emoji)

    if role_id:
        role = reaction.message.guild.get_role(role_id)
        if role:
            await user.add_roles(role)


@client.event
async def on_reaction_remove(reaction, user):
    print(f"Reaction Remove triggered by [user]")
    if user.bot:
        return

    emoji = str(reaction.emoji)
    role_id = emoji_role_map.get(emoji)

    if role_id:
        role = reaction.message.guild.get_role(role_id)
        if role:
            print(f"Remove role {role.name} from {user}")
            await user.remove_roles(role)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await tree.sync()
    print("Commands synced.")


client.run("TOKEN")
