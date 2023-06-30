import pickle


def is_picklable(obj):
    try:
        pickle.dumps(obj)
    except Exception:
        return False
    return True


if __name__ == "__main__":
    path = input("please enter the desired path")
    bk = {}
    for k in dir():
        obj = globals()[k]
        if is_picklable(obj):
            try:
                bk.update({k: obj})
            except TypeError:
                pass
    # to save session
    with open(path, 'wb') as f:
        pickle.dump(bk, f)

    # to load your session

    # import pickle
    # path = input("please enter the desired path")
    # with open(f'{path}', 'rb') as f:
    #     bk_restore = pickle.load(f)
