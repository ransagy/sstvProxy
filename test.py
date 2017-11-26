import tkinter
from tkinter import ttk

class GUI(object):
    def changeLabel(self):
        text = "You have entered " + self.someName.get()
        self.labelText.set(text)
        self.someName.delete(0, tkinter.END)
        self.someName.insert(0, "You've clicked!")

    def __init__(self):
        app = tkinter.Tk()
        app.title("GUI Test")
        app.geometry('450x300')

        self.labelText = tkinter.StringVar()
        self.labelText.set("Click when ready")
        label1 = tkinter.Label(app, textvariable=self.labelText, height=4)
        label1.pack()

        userInput = tkinter.StringVar(None)
        self.someName = tkinter.Entry(app, textvariable=userInput)
        self.someName.pack()

        button1 = tkinter.Button(app, text="Click Here", width=20,command=self.changeLabel)
        button1.pack(side='bottom',padx=15,pady=15)

        app.mainloop()

GUI() #calling the class to run
