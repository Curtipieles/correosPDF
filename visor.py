import logging
import sys
import tkinter as tk
from tkinter import scrolledtext

class ventanaEmail:
    def __init__(self, root):
        self.root = root
        self.root.title("Nuevo mensaje de correo")

        # Configurar para que sea responsive
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=0)
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_rowconfigure(4, weight=0)
        
        self.header_bg = "#1E88E5"  
        self.bg_color = "#F5F5F5"   
        self.button_color = "#1E88E5"
        
        self.root.configure(bg=self.bg_color)
        self.root.bind("<Configure>", self.on_resize) # Asegurar que los widgets se ajusten correctamente al nuevo tamaño
        
        # Crear la interfaz
        self.crear_encabezado()
        self.crear_campo_destino()
        self.crear_cuerpo()
        self.crear_piedepagina()

    def on_resize(self, event=None):
        self.root.update_idletasks()
        
    def crear_encabezado(self):
        header_frame = tk.Frame(self.root, bg=self.header_bg)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Icono de sobre
        mail_icon = tk.Label(header_frame, text="✉", font=("Arial", 16), bg=self.header_bg, fg="white")
        mail_icon.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        # Texto "New messages"
        header_label = tk.Label(header_frame, text="New messages", font=("Arial", 12, "bold"), bg=self.header_bg, fg="white")
        header_label.grid(row=0, column=1, sticky="w", padx=5, pady=10)
                
    def crear_campo_destino(self):
        # Marco
        recipient_frame = tk.Frame(self.root, bg=self.bg_color)
        recipient_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        recipient_frame.grid_columnconfigure(1, weight=1)
        
        # Campo "To"
        to_label = tk.Label(recipient_frame, text="To:", bg=self.bg_color)
        to_label.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=5)
        
        to_entry = tk.Entry(recipient_frame, bd=1, relief=tk.SOLID)
        to_entry.grid(row=0, column=1, sticky="ew", pady=5)
        
        # CC y BCC
        cc_label = tk.Label(recipient_frame, text="cc:", bg="#E0E0E0", relief=tk.SOLID, bd=1, padx=10)
        cc_label.grid(row=0, column=2, padx=5, pady=5)
        
        bcc_label = tk.Label(recipient_frame, text="bcc:", bg="#E0E0E0", relief=tk.SOLID, bd=1, padx=10)
        bcc_label.grid(row=0, column=3, padx=5, pady=5)
        
        # Campo "Subject"
        subject_frame = tk.Frame(self.root, bg=self.bg_color)
        subject_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        subject_frame.grid_columnconfigure(1, weight=1)
        
        subject_label = tk.Label(subject_frame, text="Subject:", bg=self.bg_color)
        subject_label.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=5)
        
        subject_entry = tk.Entry(subject_frame, bd=1, relief=tk.SOLID)
        subject_entry.grid(row=0, column=1, sticky="ew", columnspan=3, pady=5, padx=(0, 10))
        
    def crear_cuerpo(self):
        # Marco para el cuerpo del correo
        body_frame = tk.Frame(self.root, bg="white")
        body_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        body_frame.grid_columnconfigure(0, weight=1)
        body_frame.grid_rowconfigure(0, weight=1)
        
        # Área de texto para el correo
        text_area = scrolledtext.ScrolledText(body_frame, wrap=tk.WORD, bd=0, height=15)
        text_area.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
    def crear_piedepagina(self):
        # Marco para los botones de abajo
        footer_frame = tk.Frame(self.root, bg=self.bg_color)
        footer_frame.grid(row=4, column=0, sticky="ews", padx=10, pady=10)
        footer_frame.grid_columnconfigure(4, weight=1)
        
        # Botones de la izquierda
        attachment_btn = tk.Label(footer_frame, text="📎", font=("Arial", 14), bg=self.bg_color, cursor="hand2")
        attachment_btn.grid(row=0, column=0, padx=5)
        
        emoji_btn = tk.Label(footer_frame, text="😊", font=("Arial", 14), bg=self.bg_color, cursor="hand2")
        emoji_btn.grid(row=0, column=1, padx=5)
        
        format_btn = tk.Label(footer_frame, text="✏️", font=("Arial", 14), bg=self.bg_color, cursor="hand2")
        format_btn.grid(row=0, column=2, padx=5)
        
        image_btn = tk.Label(footer_frame, text="🖼️", font=("Arial", 14), bg=self.bg_color, cursor="hand2")
        image_btn.grid(row=0, column=3, padx=5)
        
        # Botones de la derecha
        trash_btn = tk.Label(footer_frame, text="🗑️", font=("Arial", 14), bg=self.bg_color, cursor="hand2")
        trash_btn.grid(row=0, column=5, padx=5)
        
        send_btn = tk.Button(footer_frame, text="Send", bg=self.button_color, fg="white", relief=tk.FLAT, padx=15, pady=5, cursor="hand2")
        send_btn.grid(row=0, column=6, padx=5)

def main():
    try:
        if len(sys.argv) >= 5 and len(sys.argv) <= 6:
            path = sys.argv[1]
            nit = sys.argv[2]
            tamano_letra = sys.argv[3]
            correo_origen = sys.argv[4]
            root = tk.Tk()
            root.geometry("700x500+300+100") # ("ancho", "alto", "eje x", "eje y")
            root.minsize(500, 400) #propiedad para establecer un tamaño minimo de la interface
            app = ventanaEmail(root)
            root.mainloop()
            
    except Exception as e:
        logging.error(f"Error en ejecución principal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()