import os
import shelve
import sys

sys.path.insert(0, os.getcwd())
try:
    import planarally
    import auth
except ImportError:
    print("You have to run this script from within the same folder as the save file.")
    print("E.g.: python ../scripts/convert/3_to_4.py")
    sys.exit(2)

TARGETTED_SAVE_FORMAT = 3
EXIT_SAVE_FORMAT = 4


def rename(shelf, user_map, original, new):
    user_map[new] = user_map[original]
    del user_map[original]
    user_map[new].username = new
    
    if original.lower() != new.lower():
        rooms = shelf['rooms']
        for room in rooms:
            if rooms[room].creator == original:
                rooms[room].creator = new
            if original in rooms[room].players:
                rooms[room].players[rooms[room].players.index(original)] = new
            for location in rooms[room].locations:
                for layer in rooms[room].locations[location].layer_manager.layers:
                    for sid, shape in layer.shapes.items():
                        if 'owners' not in shape: continue
                        for i, user in enumerate(shape['owners']):
                            if user == original:
                                shape['owners'][i] = new
        shelf['rooms'] = rooms


def convert(save_file):
    with shelve.open(save_file, "c", writeback=True) as shelf:
        if 'save_version' in shelf and shelf['save_version'] != TARGETTED_SAVE_FORMAT:
            print("This conversion script is meant to convert from save format {} to {}. Provided file is {}".format(
                TARGETTED_SAVE_FORMAT, EXIT_SAVE_FORMAT, shelf['save_version']))
            sys.exit(2)
        user_map = shelf['user_map']

        username_counter = {}

        for u, user in user_map.items():
            if u.lower() not in username_counter:
                username_counter[u.lower()] = []
            username_counter[u.lower()].append(u)

        print("\nFixing username casing.\n\tIf any username collisions are found they will be printed below\n\talong with the new usernames these accounts have to use.\n")

        collisions = False

        for l, u in username_counter.items():
            if len(u) > 1:
                collisions = True
                print(f'\tusername collision for {l}: {u}')
                for i, _u in enumerate(u):
                    if i == 0: 
                        print(f"\t\tusername {_u} kept intact")
                        continue
                    print(f"\t\tusername {_u} converted to {_u}{i}")
                    rename(shelf, user_map, _u, f'{_u}{i}')
        
        if not collisions:
            print("\n\tNo collisions found.")
        print("\n\nSave version increased.")

        shelf['user_map'] = user_map
        shelf['save_version'] = EXIT_SAVE_FORMAT

if __name__ == "__main__":
    convert("planar.save")
