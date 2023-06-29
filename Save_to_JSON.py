import json
import os


def is_saveable(obj):
    try:
        json.dumps(obj)
    except Exception:
        return False
    return True


def save_workspace(filename):
    """function, that saves all the workspace with json module"""
    # with open(f'{os.path.splitext(filename)[0]}.csv', 'w', encoding='UTF8', newline="") as f:
    workspace = []
    for k in dir():
        obj = globals()[k]
        if is_saveable(obj):
            try:
                workspace.append({k: obj})
            except TypeError:
                pass
    motherfile = os.path.splitext(filename)[0]
    add_text = input("please enter some additional filename-text")
    with open(f'{motherfile}{add_text}.json', 'w') as f:
        json.dump(workspace, f)
    return


def load_workspace(filename):
    """lalala"""
    return


if __name__ == "__main__":
    print("sigh")
