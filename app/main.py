import json
import os
import random
import bottle
import math

from api import ping_response, start_response, move_response, end_response

@bottle.route('/')
def index():
    return '''
    Battlesnake documentation can be found at
       <a href="https://docs.battlesnake.io">https://docs.battlesnake.io</a>.
    '''

@bottle.route('/static/<path:path>')
def static(path):
    """
    Given a path, return the static file located relative
    to the static folder.

    This can be used to return the snake head URL in an API response.
    """
    return bottle.static_file(path, root='static/')

@bottle.post('/ping')
def ping():
    """
    A keep-alive endpoint used to prevent cloud application platforms,
    such as Heroku, from sleeping the application instance.
    """
    return ping_response()

@bottle.post('/start')
def start():
    data = bottle.request.json
    data['name'] = 'Letty The Hazard Spaghetti'
    data['taunt'] = 'HISSSSSSsssssss'
    head_url = '%s://%s/static/head.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )

    lettyData = {
        'color': '#735DEC',
        'secondary_color': '#E6E6FA',
        'taunt': 'HISSSSSSsssssss',
        'head_url': head_url,
        'head_type': "smile",
        'tail_type': "curled",
    }

    print(json.dumps(data))
    print lettyData
    return lettyData

def find_food(directions):
    data = bottle.request.json
    our_snek = bottle.request.json['you']
    food_list = bottle.request.json['food']
    head_position = {
        'x': our_snek['body']['data'][0]['x'],
        'y': our_snek['body']['data'][0]['y']
    }

    closest_food_results = find_closest_food(food_list)
    closer_snake = check_for_closer_snake(closest_food_results['food'], head_position, closest_food_results['distance'])
    while(closer_snake):
        food_list['data'].remove(closest_food_results['food'])
        closest_food_results = find_closest_food(food_list)
        #if we are not closer to any of the food
        if closest_food_results['food'] is None:
            return directions
        closer_snake = check_for_closer_snake(closest_food_results['food'], head_position, closest_food_results['distance'])
    closest_food = closest_food_results['food']
    if 'left' in directions and head_position['x'] < closest_food['x']:
        directions.remove('left')
    if 'right' in directions and head_position['x'] > closest_food['x']:
        directions.remove('right')
    if 'up' in directions and head_position['y'] < closest_food['x']:
        directions.remove('up')
    if 'down' in directions and head_position['y'] > closest_food['y']:
        directions.remove('down')

    return directions

def find_closest_food(food):
    shortest_distance = 1000
    closest_food = None
    food_list = bottle.request.json['food']
    our_snek = bottle.request.json['you']

    head_position = {
        'x': our_snek['body']['data'][0]['x'],
        'y': our_snek['body']['data'][0]['y']
    }
    #find closest food
    for food in food_list['data']:
        x_distance = abs(head_position['x'] - food['x'])
        y_distance = abs(head_position['y'] - food['y'])
        total_distance = math.sqrt((x_distance**2)+(y_distance**2))
        if closest_food is None:
            shortest_distance = total_distance
            closest_food = food
        if total_distance < shortest_distance:
            shortest_distance = total_distance
            closest_food = food
    return {'food': closest_food, 'distance': shortest_distance}

def check_for_closer_snake(food, our_snek_head, our_distance):
    all_sneks = bottle.request.json['snakes']
    for snek in all_sneks['data']:
        snek_head = snek['body']['data'][0]
        #don't check our snake
        if snek_head['x'] == our_snek_head['x'] and snek_head['y'] == our_snek_head['y']:
            continue
        x_distance = abs(snek_head['x'] - food['x'])
        y_distance = abs(snek_head['y'] - food['y'])
        total_distance = math.sqrt((x_distance**2)+(y_distance**2))
        if total_distance < our_distance:
            return True
    return False

# Do not hit walls
def do_not_hit_walls(directions):
    data = bottle.request.json
    our_snek = bottle.request.json['you']
    board_width = data.get('width')
    board_height = data.get('height')

    head_position = {
        'x': our_snek['body']['data'][0]['x'],
        'y': our_snek['body']['data'][0]['y']
    }

    if 'left' in directions and head_position['x'] == 0:
        directions.remove('left')
    if 'right' in directions and head_position['x'] == (board_width-1):
        directions.remove('right')
    if 'up' in directions and head_position['y'] == 0:
        directions.remove('up')
    if 'down' in directions and head_position['y'] == (board_height-1):
        directions.remove('down')

    return directions

def find_best_move(directions):
    our_snek = bottle.request.json['you']
    health = our_snek['health']

    directions = avoid_other_sneks(directions)
    directions = do_not_hit_walls(directions)
    possible_directions = list(directions)

    if health <= 50:
        directions = find_food(directions)

    if len(directions)==0:
        directions = possible_directions

    direction = random.choice(directions)

    return direction

def avoid_other_sneks(directions):
    our_snek = bottle.request.json['you']
    head_position = {
        'x': our_snek['body']['data'][0]['x'],
        'y': our_snek['body']['data'][0]['y']
    }
    all_sneks = bottle.request.json['snakes']
    #don't hit another snek
    for snek in all_sneks['data']:
        head = snek['body']['data'][0]
        for positions in snek['body']['data']:
            x = positions['x']
            y = positions['y']
            if 'left' in directions and y == head_position['y'] and x == head_position['x']-1:
                directions.remove('left')
            if 'right' in directions and y == head_position['y'] and x == head_position['x']+1:
                directions.remove('right')
            if 'up' in directions and x == head_position['x'] and y == head_position['y']-1:
                directions.remove('up')
            if 'down' in directions and x == head_position['x'] and y == head_position['y']+1:
                directions.remove('down')
        possible_directions = list(directions)
        #don't move where other snake's head could move
        x = head['x']
        y = head['y']
        if x == head_position['x'] and y == head_position['y']:
            continue
        possible_new_positions = [
            {'x': x+1, 'y':y},
            {'x': x-1, 'y':y},
            {'x': x, 'y':y+1},
            {'x': x, 'y':y-1},
        ]
        if 'left' in directions and {'x': head_position['x']-1, 'y': head_position['y']} in possible_new_positions:
            directions.remove('left')
        if 'right' in directions and {'x': head_position['x']+1, 'y': head_position['y']} in possible_new_positions:
            directions.remove('right')
        if 'up' in directions and {'x': head_position['x'], 'y': head_position['y']-1} in possible_new_positions:
            directions.remove('up')
        if 'down' in directions and {'x': head_position['x'], 'y': head_position['y']+1} in possible_new_positions:
            directions.remove('down')
        #in case we removed all directions
        if len(directions) == 0:
            directions = possible_directions
    return directions

@bottle.post('/move')
def move():
    data = bottle.request.json

    directions = ['up', 'down', 'left', 'right']

    direction = find_best_move(directions)

    return move_response(direction)


@bottle.post('/end')
def end():
    data = bottle.request.json

    """
    TODO: If your snake AI was stateful,
        clean up any stateful objects here.
    """

    return end_response()

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug=os.getenv('DEBUG', True)
    )
