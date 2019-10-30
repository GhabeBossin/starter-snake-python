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

    """
    TODO: If you intend to have a stateful snake AI,
            initialize your snake state here using the
            request's data if necessary.
    """
    #print(json.dumps(data))

    color = "#00FF00"

    return start_response(color)

def find_food(directions):
    data = bottle.request.json
    our_snek = bottle.request.json['you']
    food_list = bottle.request.json['food']
    head_position = {
        'x': our_snek['body']['data'][0]['x'],
        'y': our_snek['body']['data'][0]['y']
    }

    for food in food_list['data']:
        if 'left' in directions and head_position['x'] < food['x']:
            directions.remove('left')
        if 'right' in directions and head_position['x'] > food['x']:
            directions.remove('right')
        if 'up' in directions and head_position['y'] < food['x']:
            directions.remove('up')
        if 'down' in directions and head_position['y'] > food['y']:
            directions.remove('down')

    return directions

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
    directions = find_food(directions)

    directions = do_not_hit_walls(directions)

    direction = random.choice(directions)

    return direction

@bottle.post('/move')
def move():
    data = bottle.request.json
    #print(json.dumps(data))

    our_snek = bottle.request.json['you']
    head_position = {
        'x': our_snek['body']['data'][0]['x'],
        'y': our_snek['body']['data'][0]['y']
    }

    directions = ['up', 'down', 'left', 'right']

    all_sneks = bottle.request.json['snakes']

    #don't hit another snek
    for snek in all_sneks['data']:
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

    direction = find_best_move(directions)

    return move_response(direction)


@bottle.post('/end')
def end():
    data = bottle.request.json

    """
    TODO: If your snake AI was stateful,
        clean up any stateful objects here.
    """
    #print(json.dumps(data))

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
