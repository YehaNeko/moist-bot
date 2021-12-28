import discord
from discord.ext import commands

calc_debug = []
ranges_debug = []


class Pfgun2(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(enabled=False, brief="**DEBUG** Do not use.")
    async def pfgun2(self, ctx, close_damage: str, long_damage: str, close_range: float, long_range: float,
                     multiplier: float, rpm: float = None):

        global calc_debug
        d1 = close_damage
        d2 = long_damage
        r1 = close_range
        r2 = long_range

        # Remove decimal places
        rmv_dcml = lambda d: round(d) if int(str(d).split(".")[1]) == 0 else round(d, 2)

        def add_ttk(_rpm, _shot):
            if rpm is not None:
                ttk = (60 * (_shot - 1)) / _rpm
                return "\n" + str(round(ttk, 5)) + "s to kill" if ttk != 0 else ""
            return ""

        def add_dps(_d1, _d2):
            dps = lambda d: (rpm / 60) * d

            if rpm is not None:
                _d1 = rmv_dcml(dps(_d1))
                _d2 = rmv_dcml(dps(_d2))

                return f"\n {_d1} to {_d2}"
            return ""

        # Embed start #
        embed = discord.Embed(title="Damage ranges", url="https://youtu.be/dQw4w9WgXcQ", color=0x00ff40)
        embed.set_footer(text="Prototype")
        prev_range_value = 0

        shots_to_damage = {
            1: "100",
            2: "50",
            3: "33.34",
            4: "25",
            5: "20",
            6: "16.67",
            7: "14.29",
            8: "12.5",
            9: "11.12",
            10: "10",
            11: "9.1",
            12: "8.34",
        }
        for n in range(1, len(shots_to_damage) + 1):
            print(n)

        # Calculate ranges #
        def calculate_range(shot, dmg_close, dmg_long):

            # Damage drop per stud
            dmg_drop_per_stud = (dmg_close - dmg_long) / (r2 - r1)

            # leftover damage after kill?
            excess_dmg = dmg_close - float(shots_to_damage.get(int(shot)))

            # converts leftover damage to studs and ands it up close range damage
            studs_after_close_range_dmg = excess_dmg / dmg_drop_per_stud

            # studs to kill range
            studs_to_kill = studs_after_close_range_dmg + r1
            studs_to_kill = round(studs_to_kill, 2)

            calc_debug.append(f"dmg_drop_per_stud: {dmg_drop_per_stud}\t "
                              f"excess_dmg: {round(excess_dmg, 2)}\t "
                              f"s_a_c_r_d: {round(studs_after_close_range_dmg, 2)}\t "
                              f"studs_to_kill: {round(studs_to_kill, 2)}"
                              )

            # Match case #

            # if the calcualted range is smaller than the close range value, it's invalid
            if studs_to_kill < r1:
                return 1, studs_to_kill, shot

            elif r1 < studs_to_kill < r2 or studs_to_kill == r1:
                return 2, studs_to_kill, shot

            # break after reaching minimum damage
            elif studs_to_kill >= r2:
                return 3, studs_to_kill, shot

        # Shotgun case
        if "x" in d1 or "x" in d2:  # checks for pellets but only uses value from d1
            pass

        # Normal case
        else:
            for s in reversed(range(1, len(shots_to_damage) + 1)):
                ranges = calculate_range(s, float(d1) * multiplier, float(d2) * multiplier)

                global calc_debug
                calc_debug.append(str(ranges) + " studs")

                # Generate embed #

                # invalid range
                if ranges[0] == 1:
                    continue

                # break after reaching minimum damage
                elif ranges[0] == 3:
                    embed.add_field(name=f"{ranges[2]} shot", value=f"{prev_range_value} to **∞** studs"
                                                                    f"{add_ttk(rpm, ranges[2])}", inline=False)
                    break

                # limited range
                elif ranges[0] == 2:
                    embed.add_field(name=f"{ranges[2]} shot", value=f"{prev_range_value} to {rmv_dcml(ranges[1])} studs"
                                                                    f"{add_ttk(rpm, ranges[2])}", inline=False)
                    prev_range_value = rmv_dcml(ranges[1])

        # Send embed
        msg1 = "\n".join(calc_debug)
        calc_debug = []

        await ctx.reply(msg1)

        await ctx.reply(embed=embed)


def setup(client):
    client.add_cog(Pfgun2(client))
