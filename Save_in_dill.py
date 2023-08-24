import dill

path = "Z:/Projects/AeroCal/Measurements/PALAS_SMPS/20230710-20230713_Parameter_setting/workspace.pkl/workspace.pkl"
#input("please enter the path")

with open(path, 'wb')as f:
    dill.dump_session()

"""to open"""
#dill.load_session(path)