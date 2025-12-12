import tkinter as tk
from tkinter import filedialog, messagebox
from pypdf import PdfReader, PdfWriter
import os

class PDFSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python PDF Splitter v2")
        self.root.geometry("450x350")
        self.root.resizable(False, False)

        # Variabel
        self.file_path = tk.StringVar()
        self.split_mode = tk.StringVar(value="all") # 'all' atau 'range'
        self.page_range = tk.StringVar()

        # --- UI Layout ---
        
        # Header
        tk.Label(root, text="PDF Splitter Tool", font=("Arial", 14, "bold")).pack(pady=10)

        # 1. Bagian Pilih File
        frame_input = tk.Frame(root)
        frame_input.pack(pady=5, padx=20, fill="x")
        
        tk.Label(frame_input, text="File PDF:").pack(anchor="w")
        
        entry_frame = tk.Frame(frame_input)
        entry_frame.pack(fill="x")
        
        self.entry_path = tk.Entry(entry_frame, textvariable=self.file_path)
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        btn_browse = tk.Button(entry_frame, text="Pilih...", command=self.browse_file)
        btn_browse.pack(side="right")

        # 2. Bagian Opsi Split
        frame_options = tk.LabelFrame(root, text="Opsi Pemisahan", padx=10, pady=10)
        frame_options.pack(pady=15, padx=20, fill="x")

        # Radio Button: Split Semua
        rb_all = tk.Radiobutton(frame_options, text="Pisahkan SEMUA halaman (1 file per halaman)", 
                                variable=self.split_mode, value="all", command=self.toggle_inputs)
        rb_all.pack(anchor="w")

        # Radio Button: Custom Range
        rb_range = tk.Radiobutton(frame_options, text="Ambil halaman tertentu saja", 
                                  variable=self.split_mode, value="range", command=self.toggle_inputs)
        rb_range.pack(anchor="w")

        # Input Range (Akan disable jika mode 'all' dipilih)
        self.entry_range = tk.Entry(frame_options, textvariable=self.page_range)
        self.entry_range.pack(fill="x", padx=20, pady=(5,0))
        tk.Label(frame_options, text="Contoh: 1, 3, 5-8 (Gunakan koma atau strip)", 
                 font=("Arial", 8), fg="gray").pack(anchor="w", padx=20)

        # 3. Tombol Eksekusi
        btn_process = tk.Button(root, text="PROSES PDF", command=self.process_pdf, 
                                bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), height=2)
        btn_process.pack(pady=10, fill="x", padx=40)

        # Footer
        self.status_label = tk.Label(root, text="Siap...", bd=1, relief=tk.SUNKEN, anchor="w")
        self.status_label.pack(side="bottom", fill="x")

        # Set kondisi awal input
        self.toggle_inputs()

    def toggle_inputs(self):
        """Mengaktifkan/mematikan input range sesuai pilihan radio button"""
        if self.split_mode.get() == "range":
            self.entry_range.config(state="normal")
        else:
            self.entry_range.config(state="disabled")

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filename:
            self.file_path.set(filename)

    def parse_page_range(self, range_str, max_pages):
        """Mengubah string '1, 3-5' menjadi set {0, 2, 3, 4} (index 0-based)"""
        pages = set()
        parts = range_str.split(',')
        
        for part in parts:
            part = part.strip()
            if not part: continue
            
            if '-' in part:
                try:
                    start, end = part.split('-')
                    start, end = int(start), int(end)
                    # Handle jika user memasukkan range terbalik (5-2) atau melebihi max
                    if start > end: start, end = end, start
                    
                    # Ingat: user input 1-based, pypdf 0-based
                    # Range python itu eksklusif di akhir, jadi end harus +1 di loop, 
                    # tapi karena kita mau convert ke index (min 1), end jadi tetap.
                    for p in range(start, end + 1):
                        if 1 <= p <= max_pages:
                            pages.add(p - 1)
                except ValueError:
                    continue # Skip jika format salah
            else:
                try:
                    p = int(part)
                    if 1 <= p <= max_pages:
                        pages.add(p - 1)
                except ValueError:
                    continue
        
        return sorted(list(pages))

    def process_pdf(self):
        input_path = self.file_path.get()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Error", "File tidak valid!")
            return

        try:
            reader = PdfReader(input_path)
            total_pages = len(reader.pages)
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            dir_name = os.path.dirname(input_path)
            output_folder = os.path.join(dir_name, f"{base_name}_hasil")

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            mode = self.split_mode.get()
            
            # LOGIKA UTAMA
            if mode == "all":
                # Mode 1: Pecah semua jadi file terpisah
                for i, page in enumerate(reader.pages):
                    writer = PdfWriter()
                    writer.add_page(page)
                    output_filename = os.path.join(output_folder, f"{base_name}_page_{i+1}.pdf")
                    with open(output_filename, "wb") as f:
                        writer.write(f)
                msg = f"Berhasil memecah semua ({total_pages}) halaman."

            else:
                # Mode 2: Ambil halaman tertentu dan GABUNG jadi satu file baru
                raw_range = self.page_range.get()
                selected_indices = self.parse_page_range(raw_range, total_pages)

                if not selected_indices:
                    messagebox.showwarning("Peringatan", "Format halaman salah atau di luar jangkauan!")
                    return

                writer = PdfWriter()
                for idx in selected_indices:
                    writer.add_page(reader.pages[idx])
                
                # Simpan sebagai satu file gabungan (Extract)
                output_filename = os.path.join(output_folder, f"{base_name}_extracted.pdf")
                with open(output_filename, "wb") as f:
                    writer.write(f)
                
                msg = f"Berhasil mengekstraksi {len(selected_indices)} halaman menjadi satu file baru."

            self.status_label.config(text="Selesai.")
            messagebox.showinfo("Sukses", f"{msg}\nDisimpan di:\n{output_folder}")

        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFSplitterApp(root)
    root.mainloop()