try:
    print("Importing numpy...")
    import numpy
    print("Numpy ok")

    print("Importing scipy...")
    import scipy.signal
    print("Scipy ok")

    print("Importing sounddevice...")
    import sounddevice
    print("Sounddevice ok")

    print("Importing tkinter...")
    import tkinter
    print("Tkinter ok")

    print("Importing matplotlib...")
    import matplotlib
    import matplotlib.pyplot
    print("Matplotlib ok")

except Exception as e:
    print(f"IMPORT ERROR: {e}")
