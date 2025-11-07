# This example requires the 'message_content' intent.
import datetime
import locale
import typing as ty

import discord
from discord.message import Message
from discord.poll import Poll
from discord.embeds import Embed
import discord.ui as dui
from discord import _types

locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

# class Res(discord.interactions.InteractionResponse):

import re

def to_channel_name(text: str) -> str:
    # Minuscule
    text = text.lower()
    # Remplace espaces et underscores par des tirets
    text = re.sub(r"[ _]+", "-", text)
    # Supprime tout ce qui n’est pas lettre, chiffre ou tiret
    text = re.sub(r"[^a-z0-9\-]", "", text)
    # Supprime les tirets en début/fin
    text = text.strip("-")
    return text

def prochain_mardi():
    ajd = datetime.date.today()
    jours_av_mardi = (1 - ajd.weekday()) % 7
    proch_mardi = ajd + datetime.timedelta(days=jours_av_mardi)

    return proch_mardi


async def interesse(interaction: discord.Interaction, view: dui.LayoutView):

    guild = interaction.guild

    assert guild is not None

    print(guild.roles)

    date = prochain_mardi().strftime("%d %B %Y")

    
    role = discord.utils.get(guild.roles, name=f"Sortie {date}")
    if role is None:
        role = await guild.create_role(reason=f"Sortie cine {date}", name=f"Sortie {date}")

    member = await guild.fetch_member(interaction.user.id)

    assert member is not None

    await member.add_roles(role, reason="car sortie")

    print(guild.categories)
    print(guild.channels)

    cat_salons = discord.utils.get(guild.categories, name="Sorties")
    if cat_salons is None:
        cat_salons = await guild.create_category(
            "Sorties", 
            overwrites={
                guild.default_role:discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
        )
    sname = to_channel_name(date)

    salon = discord.utils.get(guild.channels, name=sname)
    if salon is None:
        salon = await guild.create_text_channel(
            sname, 
            category=cat_salons,
            topic=f"Salon privé pour coordonner la sortie du {date}.",
            overwrites={
                guild.default_role:discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
        )

    print(role)

    modal = dui.Modal(title="Bonjour")
    modal.add_item(dui.TextInput(label="Texte"))

    # await interaction.response.send_modal(modal)

    # await interaction.edit_original_response(view=view)

    await interaction.response.send_message(
        f"Tu as accès au salon #{sname}.", ephemeral=True
    )

class CineSondageView(dui.LayoutView):
    votes: dict[int, int]
    container: dui.Container[dui.LayoutView]
    votes_text: dui.TextDisplay[dui.LayoutView]
    message: Message

    def __init__(self, *, votes: dict[int, int], timeout: float | None = 180):

        super().__init__(timeout=None)

        self.votes = votes

        btn_oui = dui.Button[dui.LayoutView](label="Oui", custom_id="interesse", style=discord.enums.ButtonStyle.secondary, emoji="☑️")
        btn_non = dui.Button[dui.LayoutView](label="Non", custom_id="non", style=discord.enums.ButtonStyle.secondary, emoji="❌")
        btn_depend = dui.Button[dui.LayoutView](label="Ca dépend du film", custom_id="depend", style=discord.enums.ButtonStyle.secondary, emoji="🤷‍♂️")

        btn_oui.callback = self.button_interesse_callback
        btn_non.callback = self.button_non_callback
        btn_depend.callback = self.button_depend_callback

        arow = dui.ActionRow[dui.LayoutView]()
        ping = dui.TextDisplay[dui.LayoutView]("@everyone")
        text = dui.TextDisplay[dui.LayoutView](f"### Serez vous present le mardi {prochain_mardi().strftime('%d %B')} 🗳️")
        tvotes = dui.TextDisplay[dui.LayoutView]("x", id=42)
        self.container = dui.Container(text, tvotes, arow, accent_color=discord.colour.Color.ash_embed())

        self.refresh_votes()


        arow.add_item(btn_oui)
        arow.add_item(btn_non)
        arow.add_item(btn_depend)

        self.add_item(ping)
        self.add_item(self.container)
        
    async def button_interesse_callback(self, interaction: discord.Interaction):
        # await interaction.response.send_message("gg", ephemeral=True)
        self.votes[interaction.user.id] = 1
        self.refresh_votes()
        await interesse(interaction=interaction, view=self)
        await self.message.edit(view=self)

    async def button_non_callback(self, interaction: discord.Interaction):
        self.votes[interaction.user.id] = 2
        self.refresh_votes()
        await self.message.edit(view=self)
        await interaction.response.defer(ephemeral=True)
    
    async def button_depend_callback(self, interaction: discord.Interaction):
        self.votes[interaction.user.id] = 3
        self.refresh_votes()
        await interesse(interaction, self)
        await self.message.edit(view=self)

    def refresh_votes(self):
        vo = sum(1 for d in self.votes.values() if d == 1)
        vn = sum(1 for d in self.votes.values() if d == 2)
        vp = sum(1 for d in self.votes.values() if d == 3)
        tot = max(vo + vn + vp, 1)
        ro = round(vo / tot * 10)
        rn = round(vn / tot * 10)
        rp = round(vp / tot * 10)

        votext: dui.TextDisplay[dui.LayoutView] = self.container.find_item(42)
        votext.content = (f"""
**Oui**
`{'🟩'*ro}{'⬛'*(10-ro)}` {vo} • {ro}%\n
**Non**
`{'🟩'*rn}{'⬛'*(10-rn)}` {vn} • {rn}%\n
**Ca dépend du film**
`{'🟩'*rp}{'⬛'*(10-rp)}` {vp} • {rp}%\n
🗳️ {tot} votes
""")

        # self._refresh()


class InterestedButton(dui.Button[discord.ui.View]):

    async def callback(self, interaction: discord.Interaction[_types.ClientT]) -> ty.Any:
        print("bouton")
        print(interaction)

        #await interesse(interaction=interaction, view=self)

        return await super().callback(interaction)

class MyClient(discord.Client):


    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.view = CineSondageView(votes={})
        self.add_view(self.view)

    async def on_message(self, message: Message):
        if message.author == client.user:
            print(f'self message ?')
            return
    
        print(f'Message from {message.author}: {message.content}')

        if message.content.startswith("$poll"):
            print(f'Sondage demandé')

            poll = Poll(
                "serez vous présent le mardi N",
                duration=datetime.timedelta(hours=96), 
                multiple=True, )
            poll.add_answer(text="Oui", emoji="☑️")
            poll.add_answer(text="Non", emoji="❌")
            poll.add_answer(text="Ca depend du film", emoji="🤷‍♂️")

            embed = Embed(
                colour=discord.Colour.ash_embed(),
                title="Toto",
                description="Serez vous present",
                timestamp=datetime.datetime.now(),
                )
            
            embed.add_field(
                name="Bonjour", value="Ici du texte", inline=False)
            embed.add_field(
                name="Bonjour 2", value="Ici du texte encore", inline=True)
            embed.add_field(
                name="Bonjour encore", value="Ici du texte toujour", inline=True)
            
            embed.set_footer(text="footer text")

            # mess = await message.channel.send(
            #     "@everyone Pour la semaine prochaine", 
            #     poll=poll,
            #     embed=embed,
            # )
            #text = dui.TextDisplay("Pour le mardi prochain")
            #comp = dui.Container()
            #self.view.add_item(dui.Label(text="Sortie", component=text))

            #self.view.add_item(dui.ActionRow())

            view = dui.View()
            view.add_item(InterestedButton(label="Toto", ))

            msg = await message.channel.send(
                view=self.view,
            )
            self.view.message = msg

            # await message.channel.send(embed=embed)
    #async def on_

intents = discord.Intents.default()
intents.message_content = True
intents.typing = False

client = MyClient(intents=intents)

token = open('BOTTOKEN').read()

client.run(token)

