
import sys
print(sys.argv)

if len(sys.argv)>1 and sys.argv[1]=="-server":
    pass
    #TODO server here
else:
    import gui.client_ui

    gui.client_ui.start()
