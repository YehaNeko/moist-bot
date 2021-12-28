import random


# game size #
size_x, size_y = 20, 8

# pos of player #
player_x, player_y = random.randint(0, size_x), random.randint(0, size_y)

# assets #
assets = {
    "obj": "0",
    "player_obj": "1"
}


def draw_0(x, y):
    global player_x, player_y, assets
    empty_obj = assets.get("obj")
    player = assets.get("player_obj")

    line_list = []
    line = ""

    for y_cord in range(y):
        if y_cord == player_y - 1:

            for x_cord in range(x):
                if x_cord == player_x - 1:

                    line_list.append(player)
                else:
                    line_list.append(empty_obj)

        else:
            for x_cord in range(x):
                line_list.append(empty_obj)

        line_list += "\n"
        line = "".join(line_list)

    return line


print(draw_0(size_x, size_y))
