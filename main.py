import random
import asyncio
from nicegui import ui

# Grundkonstanten
columns = 9      # Anzahl der Spalten, bleibt konstant
start_col = 4    # Startspalte (Mitte)

# Konfigurationen für die verschiedenen Schwierigkeitsstufen
difficulty_settings = {
   "Einfach": {"rows": 6, "multipliers": [0.8, 0.7, 0.6, 0.55, 0.5, 0.55, 0.6, 0.7, 0.8]},
   "Mittel":  {"rows": 8, "multipliers": [1.0, 0.9, 0.8, 0.7, 0.5, 0.7, 0.8, 0.9, 1.0]},
   "Schwer":  {"rows": 12, "multipliers": [1.5, 1.3, 1.1, 0.9, 0.5, 0.9, 1.1, 1.3, 1.5]},
}

# Aktuelle Einstellungen (Standard: Mittel)
current_difficulty = "Mittel"
rows = difficulty_settings[current_difficulty]["rows"]
multipliers = difficulty_settings[current_difficulty]["multipliers"]

# UI-Elemente: Guthaben, Einsatz, Schwierigkeitsauswahl und Button
balance = 1000
balance_label = ui.label(f'Guthaben: {balance}')
bet_input = ui.input(label='Einsatz', value='100').props('type=number')

def on_difficulty_change(value: str):
   global current_difficulty, rows, multipliers
   current_difficulty = value
   config = difficulty_settings[current_difficulty]
   rows = config["rows"]
   multipliers = config["multipliers"]
   update_canvas()  # Aktualisiere das Board, um z. B. die neue Anzahl an Reihen zu berücksichtigen

# Dropdown zur Auswahl der Schwierigkeit
ui.select(options=list(difficulty_settings.keys()), value=current_difficulty,
         label='Schwierigkeitsstufe', on_change=lambda e: on_difficulty_change(e.value))

# Parameter für die SVG-Darstellung
canvas_width = 400
canvas_height = 600

def generate_svg(ball_x=None, ball_y=None):
   """
   Erzeugt den SVG-Code für das Plinko-Board:
     - Zeichnet die Stifte (Pegs)
     - Zeichnet optional den Ball an (ball_x, ball_y)
     - Zeichnet permanent unterhalb des Boards die Multiplikatorfelder.
   """
   peg_radius = 5
   offset_x = 40
   offset_y = 60
   # Der vertikale Abstand richtet sich nach der aktuellen Anzahl an Reihen:
   row_spacing = (canvas_height - 2 * offset_y) / rows
   col_spacing = (canvas_width - 2 * offset_x) / (columns - 1)

   svg_elements = []

   # Zeichne die Stifte (Pegs)
   for r in range(rows):
       for c in range(columns):
           x = offset_x + c * col_spacing
           # In ungeraden Reihen horizontal versetzt:
           if r % 2 == 1:
               x += col_spacing / 2
               if x > canvas_width - offset_x:
                   continue
           y = offset_y + r * row_spacing
           svg_elements.append(f'<circle cx="{x}" cy="{y}" r="{peg_radius}" fill="gray" />')

   # Zeichne den Ball, falls Position angegeben
   if ball_x is not None and ball_y is not None:
       ball_radius = 8
       svg_elements.append(f'<circle cx="{ball_x}" cy="{ball_y}" r="{ball_radius}" fill="red" />')

   # Zeichne die Multiplikatorfelder unterhalb des Boards
   text_y = offset_y + rows * row_spacing + 20
   for c in range(columns):
       x = offset_x + c * col_spacing
       mult = multipliers[c]
       svg_elements.append(
           f'<text x="{x}" y="{text_y}" text-anchor="middle" fill="blue" font-size="16">{mult}</text>'
       )

   svg_content = "\n".join(svg_elements)
   svg_markup = f'<svg width="{canvas_width}" height="{canvas_height}" style="border:1px solid black">{svg_content}</svg>'
   return svg_markup

# Erstelle ein HTML-Element zur Anzeige des SVGs (Parameter 'content')
html_canvas = ui.html(content=generate_svg())

def update_canvas(ball_x=None, ball_y=None):
   """Aktualisiert das HTML-Element mit dem aktuellen SVG-Markup."""
   html_canvas.content = generate_svg(ball_x, ball_y)

async def simulate_ball():
   """Simuliert den Ballfall, aktualisiert das Guthaben und animiert den Ball auf dem Board."""
   global balance
   try:
       bet = float(bet_input.value)
   except ValueError:
       ui.notify('Ungültiger Einsatz!')
       return

   if bet > balance:
       ui.notify('Nicht genügend Guthaben!')
       return

   # Einsatz abziehen
   balance -= bet
   balance_label.set_text(f'Guthaben: {balance}')

   offset_x = 40
   offset_y = 60
   row_spacing = (canvas_height - 2 * offset_y) / rows
   col_spacing = (canvas_width - 2 * offset_x) / (columns - 1)

   # Startposition: Mitte
   current_col = start_col

   update_canvas()

   # Ballfall-Animation (0.5 Sek. Pause pro Reihe, damit der Ball sichtbar bleibt)
   for r in range(rows):
       x = offset_x + current_col * col_spacing
       y = offset_y + r * row_spacing
       update_canvas(x, y)
       await asyncio.sleep(0.5)  # Verlangsamt die Animation für bessere Sichtbarkeit
       # An den Rändern nur eine Richtung möglich
       if current_col == 0:
           move = 1
       elif current_col == columns - 1:
           move = -1
       else:
           move = random.choice([-1, 1])
       current_col += move

   # Endposition des Balls
   final_x = offset_x + current_col * col_spacing
   final_y = offset_y + rows * row_spacing
   update_canvas(final_x, final_y)

   # Gewinn berechnen und Guthaben aktualisieren
   multiplier = multipliers[current_col]
   win_amount = bet * multiplier
   balance += win_amount
   balance_label.set_text(f'Guthaben: {balance}')
   ui.notify(f'Der Ball landete im Slot {current_col} mit Multiplikator {multiplier}. Du gewinnst {win_amount} Spielgeld!')

# Button zum Starten der Simulation
ui.button('Ball fallen lassen', on_click=lambda: asyncio.create_task(simulate_ball()))

# Button für Autoplay (simuliert automatisch das Spiel nach einem bestimmten Zeitintervall)
async def autoplay():
   while True:
       await asyncio.sleep(5)  # Alle 5 Sekunden automatisch spielen
       await simulate_ball()

ui.button('Autoplay starten', on_click=lambda: asyncio.create_task(autoplay()))

# Initiale Anzeige des Boards
update_canvas()

# Zentriert das Layout und setzt den Inhalt in einem Container
ui.html("""
   <style>
       body { display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
       .nicegui { display: flex; flex-direction: column; align-items: center; }
   </style>
""")

ui.run()
