import pickle, json


def write_pickle(data: dict, path: str):
    with open(path, 'wb') as file:
        pickle.dump(data, file)

def read_pickle(path: str) -> dict:
    data = {}
    with open(path, 'rb') as file:
        try:
            data = pickle.load(file)
        except:
            pass
    
    return data

def write_json(data: dict | list, path: str) -> None:
    with open(path, 'w') as file:
        json.dump(data, file)
    
def read_json(path: str) -> dict | list:
    with open(path, 'r') as file:
        data: dict | list = json.load(file)
    return data
