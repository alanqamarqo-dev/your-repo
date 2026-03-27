import tkinter as tk

class CalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Calculator")

        self.expression = ""
        self.input_text = tk.StringVar()

        EntryField = tk.Entry(root, font=('Arial', 20, 'bold'), textvariable=self.input_text, width=15, bd=20, insertwidth=4, bg="powder blue", justify='right')     
        EntryField.grid(row=0, columnspan=4)

        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2),     
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2),     
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2),     
            ('0', 4, 1), ('+', 1, 3), ('-', 2, 3),     
            ('*', 3, 3), ('/', 4, 3), ('=', 4, 2)      
        ]

        for (text, row, col) in buttons:
            button = tk.Button(root, text=text, width=10, height=3, command=lambda t=text: self.click(t))     
            button.grid(row=row, column=col)

    def click(self, text):
        if text == '=':
            try:
                self.expression = str(eval(self.expression))
            except Exception as e:
                self.expression = "Error"
        else:
            self.expression += str(text)

        self.input_text.set(self.expression)

if __name__ == '__main__':
    root = tk.Tk()
    calculator = CalculatorGUI(root)
    root.mainloop()
