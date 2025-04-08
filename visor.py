import logging
import sys
import tkinter as tk
from tkinter import scrolledtext
from src.enviar_correo import EnviadorCorreo
import src.config as cfg

class ventanaEmail:
    def __init__(self, root, path, nit, tamano_letra, correo_origen, correo_destino, asunto, cuerpo):
        self.root = root
        self.root.title("Nuevo mensaje de correo")

        # Definir la fuente para toda la aplicación - ignorando el parámetro tamano_letra
        self.font_family = "Helvetica"  # Una fuente sans-serif moderna y limpia
        self.normal_font = (self.font_family, 10)  # Tamaño fijo para la interfaz
        self.bold_font = (self.font_family, 10, "bold")
        self.large_font = (self.font_family, 14)  # Para íconos y encabezados

        self.path = path
        self.nit = nit
        self.tamano_letra = tamano_letra  # Seguimos guardando el parámetro por si se usa en otro lugar
        self.correo_origen = correo_origen
        self.correo_destino = correo_destino
        self.asunto = asunto
        self.cuerpo = cuerpo

        self.from_entry = None
        self.to_entry = None
        self.subject_entry = None
        self.body_entry = None
        self.attachment_label = None

        # Configurar para que sea responsive
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=0)  # Encabezado
        self.root.grid_rowconfigure(1, weight=0)  # De
        self.root.grid_rowconfigure(2, weight=0)  # Para
        self.root.grid_rowconfigure(3, weight=0)  # Asunto
        self.root.grid_rowconfigure(4, weight=1)  # Cuerpo del correo
        self.root.grid_rowconfigure(5, weight=0)  # Pie de página        
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
        
        mail_icon = tk.Label(header_frame, text="✉", font=self.large_font, bg=self.header_bg, fg="white")
        mail_icon.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        header_label = tk.Label(header_frame, text="Nuevo mensaje", font=self.bold_font, bg=self.header_bg, fg="white")
        header_label.grid(row=0, column=1, sticky="w", padx=5, pady=10)
                
    def crear_campo_destino(self):
        # Campo "De"
        from_frame = tk.Frame(self.root, bg=self.bg_color)
        from_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        from_frame.grid_columnconfigure(1, weight=1)
        from_label = tk.Label(from_frame, text="De:", font=self.normal_font, bg=self.bg_color)
        from_label.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=5)
        self.from_entry = tk.Entry(from_frame, bd=1, relief=tk.SOLID, font=self.normal_font)
        self.from_entry.grid(row=0, column=1, sticky="ew", pady=5)
        if self.correo_origen:
            self.from_entry.insert(0, self.correo_origen)
            self.from_entry.config(state="readonly")
        
        # Campo "Para"        
        recipient_frame = tk.Frame(self.root, bg=self.bg_color)
        recipient_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        recipient_frame.grid_columnconfigure(1, weight=1)
        to_label = tk.Label(recipient_frame, text="Para:", font=self.normal_font, bg=self.bg_color)
        to_label.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=5)
        self.to_entry = tk.Entry(recipient_frame, bd=1, relief=tk.SOLID, font=self.normal_font)
        self.to_entry.grid(row=0, column=1, sticky="ew", pady=5)
        if self.correo_destino:
            self.to_entry.insert(0, self.correo_destino)
            self.to_entry.config(state="readonly")
        
        # CC y BCC
        cc_label = tk.Label(recipient_frame, text="cc:", font=self.normal_font, bg="#E0E0E0", relief=tk.SOLID, bd=1, padx=10)
        cc_label.grid(row=0, column=2, padx=5, pady=5)
        bcc_label = tk.Label(recipient_frame, text="bcc:", font=self.normal_font, bg="#E0E0E0", relief=tk.SOLID, bd=1, padx=10)
        bcc_label.grid(row=0, column=3, padx=5, pady=5)

        # Campo "Asunto"
        subject_frame = tk.Frame(self.root, bg=self.bg_color)
        subject_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        subject_frame.grid_columnconfigure(1, weight=1)
        subject_label = tk.Label(subject_frame, text="Asunto:", font=self.normal_font, bg=self.bg_color)
        subject_label.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=5)
        self.subject_entry = tk.Entry(subject_frame, bd=1, relief=tk.SOLID, font=self.normal_font)
        self.subject_entry.grid(row=0, column=1, sticky="ew", columnspan=3, pady=5, padx=(0, 10))
        if self.asunto:
            self.subject_entry.insert(0, self.asunto)
            self.subject_entry.config(state="readonly")

    def crear_cuerpo(self):
        # Campo "Cuerpo"
        body_frame = tk.Frame(self.root, bg="white")
        body_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
        body_frame.grid_columnconfigure(0, weight=1)
        body_frame.grid_rowconfigure(0, weight=1)
        # Usar ScrolledText para el cuerpo y asignar a la variable de clase
        self.body_entry = scrolledtext.ScrolledText(body_frame, wrap=tk.WORD, bd=1, height=15, font=self.normal_font)
        self.body_entry.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)        
        if self.cuerpo:
            self.body_entry.insert(tk.END, self.cuerpo)
            self.body_entry.config(state="disabled")
        
    def crear_piedepagina(self):
        # Marco para los botones de abajo
        footer_frame = tk.Frame(self.root, bg=self.bg_color)
        footer_frame.grid(row=5, column=0, sticky="ews", padx=10, pady=10)
        footer_frame.grid_columnconfigure(4, weight=1)
        
        # Botones de la izquierda
        attachment_btn = tk.Label(footer_frame, text="📎", font=self.large_font, bg=self.bg_color, cursor="hand2")
        attachment_btn.grid(row=0, column=0, padx=5)
        
        emoji_btn = tk.Label(footer_frame, text=f'{self.nit}.pdf', font=self.normal_font, bg=self.bg_color, cursor="hand2")
        emoji_btn.grid(row=0, column=1, padx=5)

        trash_btn = tk.Label(footer_frame, text="🗑️", font=self.large_font, bg=self.bg_color, cursor="hand2")
        trash_btn.grid(row=0, column=5, padx=5)
        
        send_btn = tk.Button(footer_frame, text="Send", font=self.normal_font, bg=self.button_color, fg="white", relief=tk.FLAT, padx=15, pady=5, cursor="hand2")
        send_btn.grid(row=0, column=6, padx=5)

def main():
    try:
        if len(sys.argv) >= 5 and len(sys.argv) <= 6:
            path = sys.argv[1]
            nit = sys.argv[2]
            tamano_letra = sys.argv[3]
            correo_origen = sys.argv[4]
            correo_destino = EnviadorCorreo.obtener_correo_por_nit(nit, cfg.ARCHIVO_DIRECCIONES)
            info = EnviadorCorreo.obtener_info_correo(cfg.ARCHIVO_INFO_CORREOS)
            asunto, cuerpo = (info.asunto, info.cuerpo) if info else ("", "")
            if not correo_destino:
                return False
            
            root = tk.Tk()
            root.geometry("700x500+300+100") # ("ancho", "alto", "eje x", "eje y")
            root.minsize(500, 400) #propiedad para establecer un tamaño minimo de la interface
            app = ventanaEmail(root, path, nit, tamano_letra, correo_origen, correo_destino, asunto, cuerpo)
            root.mainloop()
            
    except Exception as e:
        logging.error(f"Error en ejecución principal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()