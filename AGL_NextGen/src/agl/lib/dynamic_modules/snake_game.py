import tkinter as tk
import random

class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("AGL Snake Game")
        self.width = 500
        self.height = 500
        self.cell_size = 20
        
        # إعداد اللوحة
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, bg="black")
        self.canvas.pack()
        
        # حالة اللعبة
        self.snake = [(100, 100), (80, 100), (60, 100)]
        self.food = self.spawn_food()
        self.direction = "Right"
        self.score = 0
        self.game_over = False
        
        # التحكم
        self.root.bind("<Key>", self.change_direction)
        
        # بدء اللعبة
        self.run_game()

    def spawn_food(self):
        x = random.randint(0, (self.width // self.cell_size) - 1) * self.cell_size
        y = random.randint(0, (self.height // self.cell_size) - 1) * self.cell_size
        return (x, y)

    def change_direction(self, event):
        key = event.keysym
        if key == "Up" and self.direction != "Down":
            self.direction = "Up"
        elif key == "Down" and self.direction != "Up":
            self.direction = "Down"
        elif key == "Left" and self.direction != "Right":
            self.direction = "Left"
        elif key == "Right" and self.direction != "Left":
            self.direction = "Right"

    def run_game(self):
        if self.game_over:
            self.canvas.create_text(self.width/2, self.height/2, text=f"GAME OVER\nScore: {self.score}", fill="white", font=("Arial", 20))
            return

        # تحريك الثعبان
        head_x, head_y = self.snake[0]
        
        if self.direction == "Up": head_y -= self.cell_size
        elif self.direction == "Down": head_y += self.cell_size
        elif self.direction == "Left": head_x -= self.cell_size
        elif self.direction == "Right": head_x += self.cell_size
        
        new_head = (head_x, head_y)

        # التحقق من التصادم (الجدران أو النفس)
        if (head_x < 0 or head_x >= self.width or 
            head_y < 0 or head_y >= self.height or 
            new_head in self.snake):
            self.game_over = True
        else:
            self.snake.insert(0, new_head)
            
            # التحقق من الأكل
            if new_head == self.food:
                self.score += 1
                self.food = self.spawn_food()
            else:
                self.snake.pop()

        # الرسم
        self.canvas.delete("all")
        
        # رسم الطعام
        self.canvas.create_oval(self.food[0], self.food[1], self.food[0]+self.cell_size, self.food[1]+self.cell_size, fill="red")
        
        # رسم الثعبان
        for segment in self.snake:
            self.canvas.create_rectangle(segment[0], segment[1], segment[0]+self.cell_size, segment[1]+self.cell_size, fill="green")
        
        # إعادة التحديث بعد 100 ميلي ثانية
        self.root.after(100, self.run_game)

if __name__ == "__main__":
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()
